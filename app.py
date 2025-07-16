from flask import Flask, request, jsonify, render_template, session, send_from_directory, redirect
import json
import logging
import datetime
import functools
from flask_caching import Cache
from functools import wraps
from config import ADMIN_PASSWORD 
import database
import services
from collections import Counter
from config import FLASK_SECRET_KEY
from utils import get_indian_state_from_gps, get_district_from_gps

app = Flask(__name__, template_folder='.')
app.secret_key = FLASK_SECRET_KEY

config = {"CACHE_TYPE": "SimpleCache", "CACHE_DEFAULT_TIMEOUT": 3600}
app.config.from_mapping(config)
cache = Cache(app)

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

with app.app_context():
    cache.clear()
    logger.info("Application cache cleared on startup.")
    
    database.init_connection_pool()
    # CORRECTED LINE:
    services.load_datasets() # We only need to load the CSVs now
    services.init_cache(cache)
    database.create_tables()

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'logged_in' not in session:
            return jsonify({"success": False, "error": "Unauthorized"}), 401
        return view(**kwargs)
    return wrapped_view

def login_required_page(f):
    """
    Decorator for routes that render a page.
    If the user is not logged in, it redirects them to the landing page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            return redirect('/') # Redirect to the landing page
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def landing():
    return render_template('index.html')

@app.route('/app')
def app_page():
    return render_template('app.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)

# --- Authentication Routes (No Changes) ---
@app.route('/api/login', methods=['POST'])
def login():
    username, password = request.json.get('username'), request.json.get('password')
    response_data, status_code = database.login_user(username, password)
    if response_data.get("success"):
        session['logged_in'] = True
        session['user_id'] = response_data['user_id']
        session['username'] = response_data['username']
    return jsonify(response_data), status_code

@app.route('/api/register', methods=['POST'])
def register():
    username, password = request.json.get('username'), request.json.get('password')
    response, status_code = database.register_user(username, password)
    if response.get("success"):
        session['logged_in'] = True
        session['user_id'] = response['user_id']
        session['username'] = response['username']
    return jsonify(response), status_code

@app.route('/api/logout', methods=['POST'])
@login_required
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out successfully."})

@app.route('/api/check_auth', methods=['GET'])
def check_auth():
    is_authenticated = 'logged_in' in session and session.get('logged_in')
    return jsonify({"isAuthenticated": is_authenticated, "username": session.get('username') if is_authenticated else None})

@app.route('/api/dashboard_summary', methods=['GET'])
@login_required
def dashboard_summary():
    user_id = session['user_id']
    lang = request.args.get('lang', 'en')
    summary_data = services.get_dashboard_data(user_id, lang)
    
    if summary_data.get("success"):
        return jsonify(summary_data)
    else:
        return jsonify(summary_data), 500

@app.route('/api/analyze_crop', methods=['POST'])
@login_required
def analyze_crop():
    if 'image' not in request.files: return jsonify({"success": False, "error": "No image provided."}), 400
    
    # Call the service which now handles everything, including AI advice
    analysis_result = services.analyze_crop_health(request.files['image'].read())

    if "error" in analysis_result: 
        return jsonify({"success": False, "error": analysis_result["error"]}), 500
    
    # The detailed_advice is now part of the result from the service
    if not analysis_result.get("is_healthy"):
        disease_name = analysis_result.get('prediction')
        ai_prompt = (
            f"You are an expert agronomist creating a concise guide for an Indian farmer whose crop has **{disease_name}**."
            f"Follow these rules STRICTLY:\n"
            f"1. The ENTIRE response MUST be under 350 words.\n"
            f"2. Use simple, direct language. Avoid jargon.\n"
            f"3. Focus ONLY on the most critical, actionable steps for treatment and prevention.\n"
            f"4. Structure the output using this exact format: **Description:** ... ## **Symptoms:** ... ## **Treatment:** ... ## **Prevention:** ...\n"
            f"5. Under Treatment and Prevention, use a simple numbered list (e.g., 1., 2., 3.) for the key actions."
        )
        analysis_result['detailed_advice'] = services.get_gemini_report_advice(ai_prompt)
    else:
        analysis_result['detailed_advice'] = "The plant appears healthy. Continue standard monitoring."
        
    return jsonify({"success": True, "result": analysis_result})

@app.route('/api/analyze_field', methods=['POST'])
@login_required
def analyze_field():
    try:
        latitude, longitude = float(request.form.get('latitude')), float(request.form.get('longitude'))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "Invalid coordinates."}), 400
    
    image_file = request.files.get('image')
    if not image_file: return jsonify({"success": False, "error": "A soil image is required."}), 400
    
    soil_analysis = services.analyze_soil_type(image_file.read())
    if "error" in soil_analysis: return jsonify({"success": False, "error": soil_analysis["error"]}), 500
    
    lang = request.form.get('lang', 'en')
    state = get_indian_state_from_gps(latitude, longitude)
    weather = services.get_weather_data(latitude, longitude)
    historical_weather = services.get_historical_weather_summary(latitude, longitude, lang=lang) 
    
    recommendation_data = services.get_crop_recommendations(state, soil_analysis, weather, historical_weather, request.form.get('lastCrop', ''), lang=lang)

    full_report = {
        "location": {"latitude": latitude, "longitude": longitude, "state": state, "district": get_district_from_gps(latitude, longitude)}, 
        "weather": weather,
        "historical_weather": historical_weather, 
        "soil_analysis": soil_analysis,
        "recommendations": recommendation_data,
        "generated_at": datetime.datetime.now().isoformat(),
        "lang": lang
    }
    
    recommended_crops_list = recommendation_data.get("recommended_crops", [])

    if lang == 'hi':
        ai_prompt = (
            f"आप एक विशेषज्ञ कृषि सलाहकार हैं। {state} में {soil_analysis.get('prediction')} मिट्टी वाले किसान को यह उगाने की सलाह दी गई है: {', '.join(recommended_crops_list)}। "
            f"एक 2-बिंदु वाली कार्य योजना बनाएं। कोई भी परिचयात्मक या संवादात्मक पाठ न लिखें। "
            f"प्रत्येक बिंदु का एक शीर्षक और एक विवरण होना चाहिए। "
            f"आउटपुट को सख्ती से इस प्रकार प्रारूपित करें: **शीर्षक 1:** विवरण 1 ## **शीर्षक 2:** विवरण 2"
        )
    else:
        ai_prompt = (
            f"You are an expert farming advisor. A farmer in {state} with {soil_analysis.get('prediction')} soil "
            f"has been recommended to grow: {', '.join(recommended_crops_list)}. "
            f"Generate a 2-point action plan. DO NOT write any introductory or conversational text. "
            f"Each point must have a title and a description. "
            f"Format the output strictly as follows: **Title 1:** Description 1 ## **Title 2:** Description 2"
        )

    full_report['ai_advice'] = services.get_gemini_report_advice(ai_prompt)
    
    return jsonify(full_report)

@app.route('/api/get_fertilizer_plan/<int:report_id>')
@login_required
def get_fertilizer_plan(report_id):
    user_id = session['user_id']
    report_record = database.get_report_by_id(user_id, report_id)
    
    if not report_record:
        return jsonify({"success": False, "error": "Report not found or you do not have permission to view it."}), 404
        
    try:
        report_data = report_record['report_data']
        if isinstance(report_data, str):
            report_data = json.loads(report_data)
        lang = report_data.get('lang', 'en') 
        top_crop = report_data.get("recommendations", {}).get("recommended_crops", [None])[0]
        state = report_data.get("location", {}).get("state")
        soil_type = report_data.get("soil_analysis", {}).get("prediction")

        if not all([top_crop, state, soil_type]):
            return jsonify({"success": False, "error": "Report is missing crop, state, or soil data."}), 400

        plan = services.get_fertilizer_plan_for_crop(top_crop, soil_type, state, lang=lang)
        
        if plan:
            return jsonify({"success": True, "plan": plan})
        else:
            return jsonify({"success": False, "error": f"No fertilizer data available for {top_crop} in {soil_type}."}), 404

    except Exception as e:
        logger.error(f"Error generating fertilizer plan: {e}", exc_info=True)
        return jsonify({"success": False, "error": "An internal error occurred."}), 500

@app.route('/api/locations')
def get_locations():
    return send_from_directory('data', 'state_districts.json')

@app.route('/api/mandi_prices', methods=['POST'])
@login_required
def get_prices():
    data = request.json
    price_result = services.get_mandi_prices(state=data['state'], district=data['district'], crop=data['crop'], area=float(data.get('area', 1)))
    if "error" in price_result:
        return jsonify({"success": False, "error": price_result["error"]}), 404
    else:
        return jsonify({"success": True, "result": price_result})

@app.route('/api/save_report', methods=['POST'])
@login_required
def save_report():
    data = request.json.get('report_data')
    loc = data.get('location', {})
    res, code = database.save_report_to_db(session['user_id'], loc.get('latitude'), loc.get('longitude'), json.dumps(data))
    return jsonify(res), code

@app.route('/api/reports', methods=['GET'])
@login_required
def get_reports():
    res, code = database.get_user_reports(session['user_id'])
    if res.get("success"):
        for report in res.get("reports", []):
            if isinstance(report.get('saved_at'), datetime.datetime):
                report['saved_at'] = report['saved_at'].isoformat()
    return jsonify(res), code

@app.route('/api/reports/<int:report_id>', methods=['DELETE'])
@login_required
def delete_report(report_id):
    res, code = database.delete_report_from_db(report_id, session['user_id'])
    return jsonify(res), code

@app.route('/api/change_password', methods=['POST'])
@login_required
def change_password():
    data = request.json
    res, code = database.update_user_password(session['user_id'], data.get('current_password'), data.get('new_password'))
    return jsonify(res), code

@app.route('/api/delete_account', methods=['DELETE'])
@login_required
def delete_account():
    res, code = database.delete_user_account(session['user_id'])
    if res.get("success"): session.clear()
    return jsonify(res), code

@app.route('/api/chat_with_drishti', methods=['POST'])
@login_required
def chat_with_drishti():
    data = request.json
    user_id = session['user_id']
    
    if data.get("event") == "init_chat":
        welcome_message = {
            "type": "options",
            "content": "Hello! I am Drishti, your farming expert. How can I help you today?",
            "options": [
                {"label": "Get Mandi Price", "payload": {"message": "I'd like to check a mandi price."}},
                {"label": "Create a Fertilizer Plan", "payload": {"message": "Help me create a fertilizer plan"}},
                {"label": "See My Latest Report", "payload": {"message": "Show me a summary of my last report"}},
            ]
        }
        return jsonify({"success": True, "reply": welcome_message, "history": []})

    user_message = data.get('message')
    history = data.get('history', [])
    if not user_message:
        return jsonify({"success": False, "error": "No message provided."}), 400

    # This now calls the single, correct function and gets the full history back
    reply, new_history = services.get_drishti_response(user_message, user_id, conversation_history=history)
    
    return jsonify({"success": True, "reply": reply, "history": new_history})

# --- ADMIN SECTION ---

# --- ADMIN AUTH DECORATOR ---
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            return render_template('admin_login.html')
        return f(*args, **kwargs)
    return decorated_function

# --- ADMIN ROUTES ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect('/admin') # This will now work
        else:
            return render_template('admin_login.html', error="Invalid password")
    return render_template('admin_login.html')

@app.route('/api/admin/stats')
@admin_required
def get_admin_stats():
    """Provides key statistics for the admin dashboard."""
    conn = database.get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(id) FROM users;")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(id) FROM field_reports;")
        total_reports = cursor.fetchone()[0]
        # Use PostgreSQL's interval syntax
        cursor.execute("SELECT COUNT(id) FROM field_reports WHERE saved_at >= NOW() - INTERVAL '1 day';")
        reports_last_24h = cursor.fetchone()[0]
        return jsonify({"success": True, "stats": {"total_users": total_users, "total_reports": total_reports, "reports_last_24h": reports_last_24h}})
    except Exception as e:
        logger.error(f"Error fetching admin stats: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Failed to fetch stats"}), 500
    finally:
        if conn:
            database.release_db_connection(conn)

@app.route('/api/admin/reports')
@admin_required
def get_admin_reports():
    """Provides a list of the most recent reports for the admin table."""
    conn = database.get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500
    try:
        # Use DictCursor for easy dictionary access
        cursor = conn.cursor(cursor_factory=database.DictCursor)
        # PostgreSQL uses the ->> operator to extract a JSON field as text
        query = """
        SELECT
            id, user_id, saved_at,
            report_data->>'district' AS district,
            report_data->>'state' AS state,
            report_data->'recommendations'->'recommended_crops'->>0 AS top_crop
        FROM field_reports ORDER BY saved_at DESC LIMIT 20;
        """
        cursor.execute(query)
        # Convert the list of DictRow objects to a list of standard dicts
        reports = [dict(row) for row in cursor.fetchall()]
        for report in reports:
            if isinstance(report['saved_at'], datetime.datetime):
                report['saved_at'] = report['saved_at'].strftime('%Y-%m-%d %H:%M:%S')
        return jsonify({"success": True, "reports": reports})
    except Exception as e:
        logger.error(f"Error fetching admin reports: {e}", exc_info=True)
        return jsonify({"success": False, "error": "Failed to fetch reports"}), 500
    finally:
        if conn:
            database.release_db_connection(conn)

@app.route('/api/admin/analytics/registrations')
@admin_required
def get_registration_analytics():
    """Provides user registration counts for the last 30 days."""
    conn = database.get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection failed"}), 500
    try:
        cursor = conn.cursor(cursor_factory=database.DictCursor)
        # Use PostgreSQL's CURRENT_DATE and interval syntax
        query = """
        SELECT DATE(created_at) AS registration_date, COUNT(id) AS count
        FROM users
        WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(created_at) ORDER BY registration_date;
        """
        cursor.execute(query)
        data = [dict(row) for row in cursor.fetchall()]
        labels = [row['registration_date'].strftime('%b %d') for row in data]
        counts = [row['count'] for row in data]
        return jsonify({"success": True, "labels": labels, "data": counts})
    finally:
        if conn:
            database.release_db_connection(conn)

@app.route('/api/admin/analytics/top_crops')
@admin_required
def get_top_crops_analytics():
    """Aggregates and returns the most frequently recommended crops."""
    conn = database.get_db_connection()
    if not conn:
        return jsonify({"error": "DB connection failed"}), 500
    try:
        cursor = conn.cursor()
        # Fetch the JSONB array; psycopg2 will automatically convert it to a Python list
        cursor.execute("SELECT report_data->'recommendations'->'recommended_crops' FROM field_reports;")
        all_recs_tuples = cursor.fetchall()
        
        crop_counts = Counter()
        for rec_tuple in all_recs_tuples:
            crops_list = rec_tuple[0] # The list is the first element of the tuple
            if isinstance(crops_list, list):
                crop_counts.update(crops_list)
        
        top_7_crops = crop_counts.most_common(7)
        return jsonify({"success": True, "labels": [crop[0] for crop in top_7_crops], "data": [crop[1] for crop in top_7_crops]})
    finally:
        if conn:
            database.release_db_connection(conn)

@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html', title="Admin Dashboard")

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect('/admin/login')

services.start_background_cache_updater()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)