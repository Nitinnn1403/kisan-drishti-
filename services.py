import pandas as pd
import requests
import json
import logging
import io
import os
import re
import numpy as np
#import tensorflow as tf
from PIL import Image
#from tensorflow.keras.preprocessing import image as keras_image # type: ignore
#from tensorflow.keras.applications.mobilenet_v2 import preprocess_input # type: ignore
from sklearn.metrics.pairwise import cosine_similarity
from datetime import datetime, timedelta
import inspect
import time
import threading
import database
from config import (
    DATA_GOV_IN_API_KEY, OPENWEATHERMAP_API_KEY, 
    GEMINI_API_KEY, GEMINI_API_URL,
    PLANT_HEALTH_MODEL_PATH, PLANT_HEALTH_CLASS_LABELS,
    SOIL_TYPE_MODEL_PATH, SOIL_TYPE_CLASS_LABELS,
    RECOMMEND_DATA_PATH, MACRO_NUTRIENT_DATA_PATH
)
from utils import get_indian_state_from_gps
from tools import get_tools_schema
import base64
import os

CROP_API_URL = os.getenv('CROP_API_URL')
SOIL_API_URL = os.getenv('SOIL_API_URL')
CHATBOT_API_URL = os.getenv('CHATBOT_API_URL')

SOIL_TRANSLATIONS_HI = {
    "alluvial soil": "जलोढ़ मिट्टी",
    "black soil": "काली मिट्टी",
    "clay soil": "चिकनी मिट्टी",
    "red soil": "लाल मिट्टी",
    "sandy soil": "रेतीली मिट्टी"
}

CROP_TRANSLATIONS_HI = {
    "apple": "सेब","banana": "केला",
    "barley": "जौ","blackgram": "उड़द",
    "brinjal": "बैंगन","cabbage": "पत्ता गोभी",
    "cauliflower": "फूल गोभी","chickpea": "चना",
    "coconut": "नारियल","coffee": "कॉफी",
    "cotton": "कपास","grapes": "अंगूर",
    "groundnut": "मूंगफली","jowar (sorghum)": "ज्वार",
    "jute": "जूट","kidneybeans": "राजमा",
    "lentil": "मसूर","maize": "मक्का",
    "mango": "आम","mothbeans": "मोठ",
    "mungbean": "मूंग","muskmelon": "खरबूजा",
    "mustard": "सरसों","okra": "भिंडी",
    "orange": "संतरा","paddy (rice)": "धान (चावल)",
    "papaya": "पपीता","pearl millet (bajra)": "बाजरा",
    "peas": "मटर","pigeonpeas": "अरहर",
    "pomegranate": "अनार","potato": "आलू",
    "ragi (finger millet)": "रागी","rice": "चावल",
    "rubber": "रबर","sesame": "तिल",
    "soybean": "सोयाबीन","sugarcane": "गन्ना",
    "sunflower": "सूरजमुखी","tea": "चाय",
    "tobacco": "तंबाकू","tomato": "टमाटर",
    "turmeric": "हल्दी","watermelon": "तरबूज",
    "wheat": "गेहूं"
}

logger = logging.getLogger(__name__)

cache = type('dummy_cache', (), {'memoize': lambda self, timeout=None: lambda f: f})()
def init_cache(app_cache):
    global cache
    cache = app_cache

_PLANT_HEALTH_MODEL, _SOIL_TYPE_MODEL, _RECOMMEND_DF, _MANDI_DF = None, None, None, None
_STATE_MACRO_NUTRIENTS, _CROP_NUTRIENTS_DF, _SOIL_NUTRIENTS_DF = {}, None, None
_APP_CONTEXT_STRING = "",
_DISTRICT_TO_STATE_MAP = {}
_HISTORICAL_PRICES = {}
PRICE_CACHE_DIR = "price_data_cache"

CROP_ALIASES = {'rice': 'rice|paddy',
                'wheat': 'wheat',
                'maize': 'maize|corn',
                'cotton': 'cotton',
                'sugarcane': 'sugarcane',
                'potato': 'potato'}

'''def load_ml_models():
    global _PLANT_HEALTH_MODEL, _SOIL_TYPE_MODEL
    if PLANT_HEALTH_MODEL_PATH and os.path.exists(PLANT_HEALTH_MODEL_PATH):
        try:
            _PLANT_HEALTH_MODEL = tf.keras.models.load_model(PLANT_HEALTH_MODEL_PATH)
            logger.info("Plant health model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading plant health model: {e}")
    if SOIL_TYPE_MODEL_PATH and os.path.exists(SOIL_TYPE_MODEL_PATH):
        try:
            _SOIL_TYPE_MODEL = tf.keras.models.load_model(SOIL_TYPE_MODEL_PATH)
            logger.info("Soil type model loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading soil type model: {e}")'''

def load_datasets():
    global _PLANT_HEALTH_MODEL, _SOIL_TYPE_MODEL, _RECOMMEND_DF, _STATE_MACRO_NUTRIENTS, _CROP_NUTRIENTS_DF, _SOIL_NUTRIENTS_DF, _MANDI_DF, _APP_CONTEXT_STRING, _DISTRICT_TO_STATE_MAP, _HISTORICAL_PRICES

    try:
        #if PLANT_HEALTH_MODEL_PATH and os.path.exists(PLANT_HEALTH_MODEL_PATH): _PLANT_HEALTH_MODEL = tf.keras.models.load_model(PLANT_HEALTH_MODEL_PATH)
        #if SOIL_TYPE_MODEL_PATH and os.path.exists(SOIL_TYPE_MODEL_PATH): _SOIL_TYPE_MODEL = tf.keras.models.load_model(SOIL_TYPE_MODEL_PATH)

        if RECOMMEND_DATA_PATH and os.path.exists(RECOMMEND_DATA_PATH):
            _RECOMMEND_DF = pd.read_csv(RECOMMEND_DATA_PATH)
            _RECOMMEND_DF.columns = [ col.strip().lower().replace(' ', '_') for col in _RECOMMEND_DF.columns ]
            if 'soil_type' in _RECOMMEND_DF.columns: _RECOMMEND_DF['soil_type'] = _RECOMMEND_DF['soil_type'].str.lower().str.strip()
            if 'label' in _RECOMMEND_DF.columns: _RECOMMEND_DF['label'] = _RECOMMEND_DF['label'].str.lower().str.strip()
        
        if MACRO_NUTRIENT_DATA_PATH and os.path.exists(MACRO_NUTRIENT_DATA_PATH):
            macro_df = pd.read_csv(MACRO_NUTRIENT_DATA_PATH)
            for _, row in macro_df.iterrows(): _STATE_MACRO_NUTRIENTS[row.iloc[0].strip().upper()] = {'N': row.iloc[2], 'P': row.iloc[5], 'K': row.iloc[8]}
        
        if os.path.exists('data/crop_nutrients.csv'): _CROP_NUTRIENTS_DF = pd.read_csv('data/crop_nutrients.csv'); _CROP_NUTRIENTS_DF['crop'] = _CROP_NUTRIENTS_DF['crop'].str.lower().str.strip()
        
        if os.path.exists('data/soil_nutrients.csv'): _SOIL_NUTRIENTS_DF = pd.read_csv('data/soil_nutrients.csv'); _SOIL_NUTRIENTS_DF['soil_type'] = _SOIL_NUTRIENTS_DF['soil_type'].str.lower().str.strip()
        
        static_mandi_path = os.path.join('data', 'mandi_prices.csv')
        if os.path.exists(static_mandi_path):
            try:
                _MANDI_DF = pd.read_csv(static_mandi_path)
                # Correctly clean column names with _x0020_
                _MANDI_DF.columns = [col.replace('_x0020_', ' ').strip().lower() for col in _MANDI_DF.columns]

                _MANDI_DF['modal price'] = pd.to_numeric(_MANDI_DF['modal price'], errors='coerce')
                _MANDI_DF.dropna(subset=['modal price'], inplace=True)
                
                # Correctly parse the 'arrival_date' column
                if 'arrival_date' in _MANDI_DF.columns:
                    _MANDI_DF['arrival_date'] = pd.to_datetime(_MANDI_DF['arrival_date'], dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
                else:
                    _MANDI_DF['arrival_date'] = "an earlier date"
                
                logger.info("SUCCESS: Mandi Price CSV loaded and columns cleaned.")

                normalization_map = {
                    alias.lower().strip(): standard_name 
                    for standard_name, aliases in CROP_ALIASES.items() 
                    for alias in aliases.split('|')
                }

                _MANDI_DF['commodity'] = _MANDI_DF['commodity'].str.lower().str.strip()
                _MANDI_DF['commodity'] = _MANDI_DF['commodity'].replace(normalization_map)

                _MANDI_DF['state'] = _MANDI_DF['state'].str.lower().str.strip()
                _MANDI_DF['district'] = _MANDI_DF['district'].str.lower().str.strip()

                district_groups = _MANDI_DF.groupby(['state', 'district', 'commodity'])['modal price'].mean()
                for index, avg_price in district_groups.items():
                    _HISTORICAL_PRICES[index] = round(avg_price)

                state_groups = _MANDI_DF.groupby(['state', 'commodity'])['modal price'].mean()
                for index, avg_price in state_groups.items():
                    state, commodity = index
                    _HISTORICAL_PRICES[(state, '__state_avg__', commodity)] = round(avg_price)

                logger.info(f"SUCCESS: Pre-computed {len(_HISTORICAL_PRICES)} historical price averages.")

            except Exception as e:
                logger.error(f"CRITICAL ERROR loading or parsing static mandi CSV '{static_mandi_path}': {e}")
        
        if os.path.exists('data/app_context.txt'):
            with open('data/app_context.txt', 'r', encoding='utf-8') as f: _APP_CONTEXT_STRING = f.read()
        if os.path.exists('data/district_to_state.json'):
            with open('data/district_to_state.json', 'r', encoding='utf-8') as f: _DISTRICT_TO_STATE_MAP = {k.lower(): v for k, v in json.load(f).items()}

    except Exception as e:
        logger.error(f"Failed to load data: {e}", exc_info=True)
        
def load_all_data():
    #load_ml_models()
    load_datasets()

def find_state_from_district(district: str) -> str:
    state = _DISTRICT_TO_STATE_MAP.get(district.lower().strip())
    if state:
        logger.info(f"Internal search: Found state '{state}' for district '{district}'.")
        return state
    else:
        logger.warning(f"Internal search: Could not find a state for district '{district}'.")
        return None

def analyze_crop_health(image_data):
    if not CROP_API_URL:
        return {"error": "Crop analysis service is not configured."}
    
    # Encode image to send over the internet
    b64_image = base64.b64encode(image_data).decode('utf-8')
    payload = {"data": [f"data:image/jpeg;base64,{b64_image}"]}

    try:
        response = requests.post(CROP_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        # The result from Gradio is nested under a "data" key
        return response.json().get("data", [{}])[0]
    except Exception as e:
        logger.error(f"Error calling Crop API: {e}")
        return {"error": "The AI vision service is currently unavailable."}

def analyze_soil_type(image_data):
    if not SOIL_API_URL:
        return {"error": "Soil analysis service is not configured."}

    b64_image = base64.b64encode(image_data).decode('utf-8')
    payload = {"data": [f"data:image/jpeg;base64,{b64_image}"]}
    
    try:
        response = requests.post(SOIL_API_URL, json=payload, timeout=60)
        response.raise_for_status()
        return response.json().get("data", [{}])[0]
    except Exception as e:
        logger.error(f"Error calling Soil API: {e}")
        return {"error": "The AI vision service is currently unavailable."}

def list_my_reports(user_id):
    """
    Fetches a list of all saved reports for a given user ID.
    """
    reports_data, _ = database.get_user_reports(user_id)
    if not reports_data.get("success") or not reports_data.get("reports"):
        return "You have no saved reports. You can create one from the 'Analyze Field' page."
    
    formatted_reports = []

    for report in reports_data["reports"][:5]:
        try:
            report_data = json.loads(report['report_data'])
            report_date = report['saved_at'].strftime('%b %d, %Y')

            formatted_reports.append({
                "report_id": report['id'], 
                "date": report_date,
            })
        except Exception:
            continue
            
    if not formatted_reports:
        return "You have no valid saved reports."

    return formatted_reports

# In services.py

def get_specific_report(user_id, report_id: int):
    """
    Fetches a single user report by its ID and returns a clean,
    Markdown-formatted summary.
    """
    report_record = database.get_report_by_id(user_id, report_id)
    if not report_record:
        return f"Error: I could not find a report with the ID {report_id}."
        
    try:
        report_data = json.loads(report_record['report_data'])
        loc = report_data.get('location', {})
        soil = report_data.get('soil_analysis', {})
        recs = report_data.get('recommendations', {})
        
        date_obj = report_record['saved_at']
        day = date_obj.day
        if 4 <= day <= 20 or 24 <= day <= 30:
            suffix = "th"
        else:
            suffix = ["st", "nd", "rd"][day % 10 - 1]
        formatted_date = date_obj.strftime(f'%B {day}{suffix}, %Y')

        crops_str = ', '.join(recs.get('recommended_crops', ['N/A']))
        
        summary = (
            f"**Summary for Report #{report_id}**\n"
            f"- **Date:** {formatted_date}\n"
            f"- **Location:** {loc.get('district', 'N/A')}, {loc.get('state', 'N/A')}\n"
            f"- **Soil Type:** {soil.get('prediction', 'N/A')}\n"
            f"- **Top Recommended Crops:** {crops_str}"
        )
        return summary
    except Exception as e:
        logger.error(f"Error reading report data for chatbot summary: {e}")
        return f"Error: Could not read the data for report ID {report_id}."

@cache.memoize(timeout=7200)
def get_forecast_data(latitude, longitude, lang='en'):
    """
    Fetches forecast data from OpenWeatherMap, correctly passing the language parameter.
    """
    default = {"current": {"temperature": "N/A", "humidity": "N/A", "description": "N/A"}, "forecast": []}
    if not OPENWEATHERMAP_API_KEY:
        return default

    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={OPENWEATHERMAP_API_KEY}&units=metric&lang={lang}"
    
    try:
        data = requests.get(url, timeout=10).json()

        if 'list' not in data or not data['list']:
            return default

        current = {
            "temperature": data['list'][0]['main']['temp'],
            "humidity": data['list'][0]['main']['humidity'],
            "description": data['list'][0]['weather'][0]['description']
        }

        daily = {}
        for item in data['list']:
            date = datetime.fromtimestamp(item['dt']).strftime('%Y-%m-%d')
            if date not in daily:
                daily[date] = {'max': [], 'min': [], 'icons': {}}
            daily[date]['max'].append(item['main']['temp_max'])
            daily[date]['min'].append(item['main']['temp_min'])
            daily[date]['icons'][item['weather'][0]['icon']] = daily[date]['icons'].get(item['weather'][0]['icon'], 0) + 1
            
        forecast = [{"day_name": datetime.strptime(d, '%Y-%m-%d').strftime('%a'), "temp_max": max(v['max']), "temp_min": min(v['min']), "icon": max(v['icons'], key=v['icons'].get)} for d, v in sorted(daily.items()) if d != datetime.now().strftime('%Y-%m-%d')][:5]
        
        return {"current": current, "forecast": forecast}
        
    except Exception as e:
        logger.error(f"Error fetching forecast from OpenWeatherMap: {e}")
        return default

def get_weather_data(lat, lon, lang='en'): 
    return get_forecast_data(lat, lon, lang=lang).get('current', {})

def get_historical_weather_summary(lat, lon, lang='en'):
    default = {"kharif_avg_temp": 28, "rabi_avg_temp": 22, "kharif_total_rainfall": 800, "rabi_total_rainfall": 150, "note": "Could not retrieve historical data."}
    try:
        end, start = datetime.now(), datetime.now() - timedelta(days=365)
        params = {"latitude": lat, "longitude": lon, "start_date": start.strftime('%Y-%m-%d'), "end_date": end.strftime('%Y-%m-%d'), "daily": "temperature_2m_mean,precipitation_sum"}
        res = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=20).json()['daily']
        df = pd.DataFrame(res)
        df['time'] = pd.to_datetime(df['time'])
        
        kharif = df[df.time.dt.month.isin([6,7,8,9,10])]
        rabi = df[df.time.dt.month.isin([11,12,1,2,3,4])]
        
        kharif_rain = kharif.precipitation_sum.sum()
        rabi_rain = rabi.precipitation_sum.sum()
        data_note = None

        if kharif_rain < 100 or rabi_rain < 50:
            if lang == 'hi':
                data_note = "ध्यान दें: इस स्थान के लिए ऐतिहासिक वर्षा डेटा अधूरा हो सकता है, जो सिफारिश की सटीकता को प्रभावित कर सकता है।"
            else:
                data_note = "Note: Historical rainfall data may be incomplete for this specific location, which can affect recommendation accuracy."
                    
        return {
            "kharif_avg_temp": kharif.temperature_2m_mean.mean(), 
            "rabi_avg_temp": rabi.temperature_2m_mean.mean(), 
            "kharif_total_rainfall": kharif_rain, 
            "rabi_total_rainfall": rabi_rain,
            "note": data_note
        }
    except Exception:
        return default

def get_crop_recommendations(state, soil_results, weather, historical, last_crop, lang='en'):
    if _RECOMMEND_DF is None or _RECOMMEND_DF.empty: 
        return {"recommended_crops": [], "considerations": "Recommendation data unavailable."}
    
    soil_type_prediction = soil_results.get("prediction", "unknown").lower()
    
    search_term = "clay" if "clay" in soil_type_prediction else soil_type_prediction.split(' ')[0]
    
    soil_filtered_df = _RECOMMEND_DF[_RECOMMEND_DF['soil_type'].str.contains(search_term, case=False, na=False)].copy()
    
    if soil_filtered_df.empty: 
        return {"recommended_crops": [], "considerations": f"No crop data for detected soil type: {soil_results.get('prediction')}."}
    
    is_kharif = 5 <= datetime.now().month <= 10
    
    temp = historical.get('kharif_avg_temp', 28) if is_kharif else historical.get('rabi_avg_temp', 22)
    
    rain_total = historical.get('kharif_total_rainfall', 800) if is_kharif else historical.get('rabi_total_rainfall', 150)
    
    rain_monthly = ((np.clip(rain_total, 300, 1500) / 5) if is_kharif else (np.clip(rain_total, 300, 1500) / 6))
    
    nutrients = _STATE_MACRO_NUTRIENTS.get(state.upper(), {'N': 60, 'P': 45, 'K': 45})
    
    target_vector = np.array([nutrients.get('N', 60), nutrients.get('P', 45), nutrients.get('K', 45), temp, weather.get('humidity', 65), 6.5, rain_monthly])
    
    dataset_vectors = soil_filtered_df[['n', 'p', 'k', 'temperature', 'humidity', 'ph', 'rainfall']].values
    
    soil_filtered_df['similarity'] = cosine_similarity([target_vector], dataset_vectors)[0]
    
    strong_matches_df = soil_filtered_df[soil_filtered_df['similarity'] > 0.90]
    
    if not strong_matches_df.empty:
        recs = strong_matches_df.sort_values(by='similarity', ascending=False)['label'].unique().tolist()
        if lang == 'hi':
            considerations = "आपकी मिट्टी के प्रकार और क्षेत्रीय जलवायु पर आधारित।"
        else:
            considerations = "Based on your soil type and regional climate."

    else:
        recs = soil_filtered_df.sort_values(by='similarity', ascending=False)['label'].unique().tolist()
        if lang == 'hi':
            considerations = "आपकी जलवायु असामान्य है। सिफारिशें मुख्य रूप से आपकी मिट्टी के प्रकार पर आधारित हैं।"
        else:
            considerations = "Your climate is unusual. Recommendations are based primarily on your soil type."

    if not recs: 
        return {"recommended_crops": [], "considerations": "Could not determine a suitable crop."}
    
    final_recs = [c for c in recs if c.lower() != last_crop.lower()] if last_crop else recs
    return {"recommended_crops": [c.capitalize() for c in (final_recs or recs)][:5], "considerations": considerations}


def get_fertilizer_plan_for_crop(crop_name, soil_type, state, lang='en', short_advice=False):
    if _CROP_NUTRIENTS_DF is None or _SOIL_NUTRIENTS_DF is None: return None
    crop_req_row = _CROP_NUTRIENTS_DF[_CROP_NUTRIENTS_DF['crop'] == crop_name.lower().strip()]
    if crop_req_row.empty: return None
    crop_req = crop_req_row.iloc[0]
    search_soil = soil_type.lower().strip()
    soil_nutrients_row = _SOIL_NUTRIENTS_DF[_SOIL_NUTRIENTS_DF['soil_type'].apply(lambda x: search_soil in x or x in search_soil)]
    
    # This logic for determining the note remains the same
    if not soil_nutrients_row.empty:
        available, note_en = soil_nutrients_row.iloc[0], f"based on average values for **{soil_type.title()}**."
        note_hi = f"**{soil_type.title()}** के औसत मूल्यों पर आधारित।"
    else:
        available_dict = _STATE_MACRO_NUTRIENTS.get(state.upper(), {'N': 60, 'P': 45, 'K': 45})
        available = pd.Series(available_dict).rename({'N':'n_avg', 'P':'p_avg', 'K':'k_avg'})
        note_en = f"based on average soil data for **{state.title()}**."
        note_hi = f"**{state.title()}** के औसत मिट्टी डेटा पर आधारित।"

    note = note_hi if lang == 'hi' else note_en

    n = max(0, round((crop_req['n_req'] - available.get('n_avg', 0)) / 2.471))
    p = max(0, round((crop_req['p_req'] - available.get('p_avg', 0)) / 2.471))
    k = max(0, round((crop_req['k_req'] - available.get('k_avg', 0)) / 2.471))
    plan = {"crop": crop_name.capitalize(), "n_needed": n, "p_needed": p, "k_needed": k}

    if short_advice:
        prompt = (
            f"You are a friendly farming advisor. Create a fertilizer plan for a **{plan['crop']}** crop. "
            f"The goal is to add roughly **{n}kg N**, **{p}kg P**, and **{k}kg K** per acre. "
            f"Follow these rules strictly:\n"
            f"1.  **Be very brief:** The entire response must be under 80 words.\n"
            f"2.  **Use emojis:** Add relevant emojis like 🌱, 💧, 🌾 to make it engaging.\n"
            f"3.  **Structure:** Provide a simple plan for the 'Basal' (at sowing) and 'Top-Dressing' stages.\n"
            f"4.  **Mention the source:** Start by briefly stating the advice is {note}.\n"
        )
    else:
        if lang == 'hi':
            prompt = (
                f"आप एक सहायक कृषि सलाहकार हैं। **{CROP_TRANSLATIONS_HI.get(crop_name.lower(), crop_name.capitalize())}** फसल के लिए पोषक तत्वों का लक्ष्य लगभग **{n}kg N**, **{p}kg P**, और **{k}kg K** प्रति एकड़ है। "
                f"यह सलाह {note_hi} पर आधारित है।\n\n"
                f"एक संक्षिप्त, चरण-दर-चरण आवेदन मार्गदर्शिका बनाएं। "
                f"कोई भी परिचयात्मक पाठ न लिखें। प्रत्येक बिंदु का एक शीर्षक और एक विवरण होना चाहिए। "
                f"उप-बिंदुओं के लिए बुलेट बिंदुओं का उपयोग करें। "
                f"आउटपुट को सख्ती से इस प्रकार प्रारूपित करें:\n"
                f"**शीर्षक 1:** * बुलेट बिंदुओं के साथ विवरण। ## **शीर्षक 2:** * बुलेट बिंदुओं के साथ विवरण।"
            )

        else:
            prompt = (
                f"You are a helpful farming advisor. The nutrient target for a **{plan['crop']}** crop is "
                f"roughly **{n}kg N**, **{p}kg P**, and **{k}kg K** per acre. "
                f"This advice is {note_en}.\n\n"
                f"Create a concise, step-by-step application guide. "
                f"DO NOT write any introductory text. Each point must have a title and a description. "
                f"Use bullet points for sub-items. "
                f"Format the output strictly as follows:\n"
                f"**Title 1:** Description with * bullet points. ## **Title 2:** Description with * bullet points."
            )

    plan['ai_application_advice'] = get_gemini_report_advice(prompt)
    return plan

def _fetch_live_price_data(state, for_date):
    """
    Fetches ALL records for a given state for a SPECIFIC date using the CORRECTED resource_id and date format.
    """
    if not DATA_GOV_IN_API_KEY:
        logger.warning("LIVE API FETCH SKIPPED: DATA_GOV_IN_API_KEY not set.")
        return None
    try:
        api_date_str = for_date.strftime('%Y-%m-%d')
        
        params = {
            "api-key": DATA_GOV_IN_API_KEY,
            "format": "json",
            "limit": "2000",
            "filters[state]": state.title(),
            "filters[arrival_date]": api_date_str
        }
        
        headers = { 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36' }

        correct_resource_id = '9ef84268-d588-465a-a308-a864a43d0070'
        
        logger.info(f"LIVE API FETCH: Requesting data with resource_id '{correct_resource_id}' for state '{state.title()}' on date '{api_date_str}'...")
        
        response = requests.get(f"https://api.data.gov.in/resource/{correct_resource_id}", params=params, headers=headers, timeout=20)
        
        response.raise_for_status()
        
        data = response.json()
        records = data.get("records", [])
        
        logger.info(f"LIVE API FETCH: Successfully got {len(records)} records.")
        return records
        
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error fetching live price data: {http_err} - Response: {response.text}")
        return None
    except Exception as e:
        logger.error(f"General error fetching live price data for date {for_date}: {e}", exc_info=True)
        return None

def _get_value_from_record(record, keys_to_try):
    """Helper to get a value from a record trying multiple possible keys."""
    for key in keys_to_try:
        if key in record:
            return record[key]
    return '' 

def _parse_and_average_prices(records, crop, district):
    """
    Parses records, now robustly checking for different possible key names and
    validating that each record is a dictionary before processing.
    """

    if isinstance(records, dict):
        records = list(records.values())

    if not isinstance(records, list) or not records:
        return None, None
        
    first_dict_record = next((r for r in records if isinstance(r, dict)), None)
    if first_dict_record:
        logger.info(f"DEBUG: Keys in first valid record from API: {list(first_dict_record.keys())}")
    else:
        logger.warning("DEBUG: The records list does not contain any valid dictionary objects.")

    crop_pattern = CROP_ALIASES.get(crop.lower(), crop.lower())
    district_clean = district.lower().strip()

    filtered_records = []
    for r in records:
        if isinstance(r, dict):
            if (re.search(district_clean, str(_get_value_from_record(r, ['district', 'District'])).lower()) and
                re.search(crop_pattern, str(_get_value_from_record(r, ['commodity', 'Commodity'])).lower())):
                filtered_records.append(r)
    
    logger.info(f"PARSING: Found {len(filtered_records)} records after filtering for district='{district}' and crop='{crop}'.")

    if not filtered_records:
        return None, None

    prices = []
    for r in filtered_records:
        modal_price_str = _get_value_from_record(r, ['modal_price', 'Modal Price', 'Modal_Price'])
        if modal_price_str and str(modal_price_str).replace('.', '', 1).isdigit():
            prices.append(int(float(modal_price_str)))
    
    if prices:
        avg_price = round(sum(prices) / len(prices))
        note = f"Using live market data for {district.title()}."
        logger.info(f"SUCCESS: Calculated average price of {avg_price} from {len(prices)} valid price records.")
        return avg_price, note
    
    logger.warning(f"PARSING FAILED: Found {len(filtered_records)} records but none had a valid modal price.")
    return None, None

def _read_price_from_csv_fallback(state, crop, district=None):
    if not _HISTORICAL_PRICES or _MANDI_DF is None:
        return None, None, None

    state_clean = state.lower().strip()
    district_clean = district.lower().strip()
    crop_clean = crop.lower().strip()
    
    stale_date = "a prior date"

    district_record = _MANDI_DF[(_MANDI_DF['state'] == state_clean) & (_MANDI_DF['district'] == district_clean) & (_MANDI_DF['commodity'] == crop_clean)]
    if not district_record.empty and 'arrival_date' in district_record.columns:
        stale_date = district_record.iloc[0]['arrival_date']

    price = _HISTORICAL_PRICES.get((state_clean, district_clean, crop_clean))
    
    if price:
        note = f"Using historical data for {district.title()}."
        return price, note, stale_date
        
    price = _HISTORICAL_PRICES.get((state_clean, '__state_avg__', crop_clean))

    if price:
        note = f"Could not find data for {district.title()}, using state-level historical average."
        state_record = _MANDI_DF[(_MANDI_DF['state'] == state_clean) & (_MANDI_DF['commodity'] == crop_clean)]
        if not state_record.empty and 'arrival_date' in state_record.columns:
            stale_date = state_record.iloc[0]['arrival_date']
        return price, note, stale_date

    return None, None, None

def get_chatbot_mandi_price(district: str, crop: str):
    """
    A simplified price lookup that only uses the pre-computed historical data.
    """
    state = find_state_from_district(district)
    if not state:
        return {"error": f"I couldn't identify the state for '{district}'."}

    price, note, stale_date = _read_price_from_csv_fallback(state, crop, district)

    if price:
        return {"price": price, "location": f"{district.title()}, {state.title()}", "note": note}
    else:
        return {"error": f"Sorry, I have no historical price data for {crop} in {district}."}

def _save_to_local_cache(state, records_list):
    """
    Saves the live API response data to a local JSON file in the new format,
    always including a timestamp.
    """
    try:
        if not os.path.exists(PRICE_CACHE_DIR):
            os.makedirs(PRICE_CACHE_DIR)
        
        # Construct the dictionary to be saved
        data_to_save = {
            "timestamp": datetime.now().isoformat(),
            "records": records_list
        }
        
        filepath = os.path.join(PRICE_CACHE_DIR, f"{state.lower()}_cache.json")
        with open(filepath, 'w') as f:
            json.dump(data_to_save, f)
            
        logger.info(f"Successfully saved {len(records_list)} records to local cache: {filepath}")
    except Exception as e:
        logger.error(f"Failed to save data to local cache: {e}")

# In services.py, modify _load_from_local_cache

def _load_from_local_cache(state):
    """Loads and validates data from a local JSON cache file."""
    try:
        filepath = os.path.join(PRICE_CACHE_DIR, f"{state.lower()}_cache.json")
        if not os.path.exists(filepath):
            return None # No cache file exists

        with open(filepath, 'r') as f:
            data = json.load(f)

        cache_timestamp_str = data.get("timestamp")
        if not cache_timestamp_str:
            logger.warning(f"Local cache file for '{state}' is old format (no timestamp). Ignoring.")
            return None

        cache_time = datetime.fromisoformat(cache_timestamp_str)
        if (datetime.now() - cache_time).total_seconds() > (12 * 3600):
            logger.warning(f"Local cache file '{filepath}' is older than 12 hours. Ignoring it.")
            return None
        
        logger.info(f"Successfully loaded {len(data['records'])} records from a valid local cache file.")
        return data.get("records")
        
    except Exception as e:
        logger.error(f"Failed to load data from local cache: {e}")
        return None

@cache.memoize(timeout=14400)
def _fetch_price_data(state, district, crop):
    logger.info(f"--- FETCHING PRICE for '{crop}' in '{district}, {state}' ---")
    
    cached_records = _load_from_local_cache(state)
    if cached_records:
        avg_price, note = _parse_and_average_prices(cached_records, crop, district)
        if avg_price:
            logger.info("Serving price from recent local file cache.")
            return {"price": avg_price, "note": note, "is_stale": False, "stale_date": None}

    today = datetime.now()
    yesterday = today - timedelta(days=1)
    
    live_records = _fetch_live_price_data(state, today)
    if not live_records:
        live_records = _fetch_live_price_data(state, yesterday)
    
    if live_records:
        _save_to_local_cache(state, live_records) 
        avg_price, note = _parse_and_average_prices(live_records, crop, district)
        if avg_price:
            logger.info("Serving price from live API fetch.")
            return {"price": avg_price, "note": note, "is_stale": False, "stale_date": None}

    logger.warning("All data sources failed. Falling back to static built-in CSV.")
    avg_price, note, stale_date = _read_price_from_csv_fallback(state, crop, district)
    if avg_price:
        return {"price": avg_price, "note": note, "is_stale": True, "stale_date": stale_date}
    
    return {"error": f"No market data available for '{crop}' in {state} from any source."}


def get_mandi_prices(state, district, crop, area=1.0, lang='en'): # <-- Add lang
    price_data = _fetch_price_data(state, district, crop)
    if "error" in price_data: return price_data
    price = price_data.get("price")
    yield_qpa = {'rice': 22, 'wheat': 20, 'maize': 25, 'cotton': 8, 'chickpea': 10}.get(crop.lower(), 15)
    revenue = (yield_qpa * float(area)) * price if price else 0
    
    note = price_data.get("note")
    if lang == 'hi':
        if "Using historical data" in note:
            note = f"{district.title()} के लिए ऐतिहासिक डेटा का उपयोग किया जा रहा है।"
        elif "using state-level" in note:
            note = f"{district.title()} के लिए डेटा नहीं मिला, राज्य-स्तरीय ऐतिहासिक औसत का उपयोग किया जा रहा है।"
        else:
            note = f"{district.title()} के लिए लाइव बाजार डेटा का उपयोग किया जा रहा है।"

    return {
        "crop": crop.capitalize(), "location": f"{district.title()}, {state.title()}",
        "average_mandi_price": price, "estimated_yield_qpa": yield_qpa,
        "total_estimated_revenue": round(revenue), "area_acres": float(area),
        "note": note,
        "is_stale": price_data.get("is_stale"),
        "stale_date": price_data.get("stale_date")
    }

def get_mandi_price(district: str, crop: str, state: str = None):
    """
    Fetches ONLY the price information for a crop. If state is not provided, it will be inferred from the district.
    """
    if not state:
        state = find_state_from_district(district)
        if not state:
            return {"error": f"I couldn't determine the state for the district '{district}'. Please try again and provide a state."}
    
    price_data = _fetch_price_data(state, district, crop)
    if "error" in price_data:
        return price_data

    # Return a rich dictionary with all the necessary info for formatting
    return {
        "crop": crop.capitalize(),
        "location": f"{district.title()}, {state.title()}",
        "average_mandi_price": price_data.get("price"),
        "note": price_data.get("note"),
        "is_stale": price_data.get("is_stale"),
        "stale_date": price_data.get("stale_date")
    }

def get_revenue_estimate(district: str, crop: str, area: float, state: str = None):
    """
    Fetches price data AND calculates the total estimated revenue. State is inferred if not provided.
    """
    # --- FIX: Find the state from the district if it's not provided ---
    if not state:
        state = find_state_from_district(district)
        if not state:
            return {"error": f"I couldn't determine the state for the district '{district}'. Please try again and provide a state."}

    price_data = _fetch_price_data(state, district, crop)
    if "error" in price_data:
        return price_data
        
    price = price_data.get("price")
    yield_qpa = {'rice': 22, 'wheat': 20, 'maize': 25, 'cotton': 8, 'chickpea': 10}.get(crop.lower(), 15)
    revenue = (yield_qpa * float(area)) * price if price else 0
    
    return {
        "crop": crop.capitalize(),
        "location": f"{district.title()}, {state.title()}",
        "average_mandi_price": price,
        "total_estimated_revenue": round(revenue),
        "area_acres": float(area),
        "note": price_data.get("note")
    }

def get_dashboard_price_summary(state, district, lang='en'): # <-- Add lang
    summary = {"labels": [], "prices": [], "note": ""}
    key_crops = ['Rice', 'Wheat', 'Maize', 'Cotton']
    
    translated_labels = []

    for crop in key_crops:
        # Pass lang to the function
        price_data = get_mandi_prices(state, district, crop, area=1.0, lang=lang) 
        price = price_data.get("average_mandi_price")
        
        # Translate the crop names for the chart
        if lang == 'hi':
            translated_labels.append(CROP_TRANSLATIONS_HI.get(crop.lower(), crop))
        else:
            translated_labels.append(crop)
            
        summary["prices"].append(price if price else 0)
        if price_data.get("is_stale"):
            summary["note"] = "Note: Some prices based on historical data."
            if lang == 'hi':
                summary["note"] = "ध्यान दें: कुछ मूल्य ऐतिहासिक डेटा पर आधारित हैं।"

    summary["labels"] = translated_labels # Use the translated labels
    return summary

def get_gemini_report_advice(prompt):
    """
    Gets advice from the Gemini API and parses it into a structured list.
    """
    if not GEMINI_API_KEY or not GEMINI_API_URL:
        return [{"title": "AI Advice Not Available", "description": "The AI service is not configured."}]
        
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    try:
        response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", headers=headers, json=data, timeout=30)
        response.raise_for_status()
        raw_text = response.json()["candidates"][0]["content"]["parts"][0]["text"]

        advice_parts = []
        sections = raw_text.strip().split('##')

        for section in sections:
            if ':**' in section:
                title_part, description_part = section.split(':**', 1)
                title = title_part.replace('**', '').strip()
                description = description_part.strip()
                advice_parts.append({"title": title, "description": description})
        
        return advice_parts if advice_parts else [{"title": "AI Advice", "description": raw_text}]

    except Exception as e:
        logger.error(f"Error contacting or parsing Gemini API response: {e}")
        return [{"title": "Error", "description": "Sorry, an error occurred while contacting the AI for advice."}]


def get_drishti_response(user_message, user_id, conversation_history=[]):
    if not CHATBOT_API_URL:
        return {"type": "text", "content": "Chatbot is not configured."}, conversation_history
    
    from tool_registry import AVAILABLE_TOOLS
    from tools import get_tools_schema

    system_prompt = """
    You are 'Drishti', a friendly and expert AI agricultural assistant. Your goal is to help Indian farmers.
    - Use the available tools to answer user questions about market prices, fertilizer plans, and user reports.
    - If the user's request is unclear, ask simple clarifying questions.
    - **Crucially: NEVER mention your internal tool names. NEVER rephrase or add extra conversation to the information you get back from a tool. Your only job is to present the tool's output directly.**
    - NEVER mention that you are an AI or a chatbot. You are simply 'Drishti', a helpful farming assistant.
    - **Crucially: NEVER mention [TOOL_RESULT], [END_TOOL_RESULT] etc. These are internal markers and should not be visible to the user.
    - For simple greetings like 'hello', give a short, friendly reply.
    - You do not know anything about other websites or services other than Kisan Drishti. If a user asks about something outside your knowledge, say: "I don't have information on that. I can only help with farming-related questions."
    - If a tool returns data with a 'note' field, you MUST include that information in your response, but phrase it naturally. For example, instead of just saying the note, you might say 'Based on live market data...' or 'Please note, this data is from a past date...'.
    """

    current_conversation = conversation_history + [{"role": "user", "content": user_message}]
    
    # The Gradio API expects all inputs to be strings, so we use json.dumps
    payload = {
        "data": [
            system_prompt,
            json.dumps(current_conversation),
            json.dumps(get_tools_schema())
        ]
    }
    
    try:
        # First API call to the chatbot model
        response = requests.post(CHATBOT_API_URL, json=payload, timeout=90)
        response.raise_for_status()
        
        # Gradio returns a JSON string, which we need to parse
        api_result_str = response.json().get("data")[0]
        ai_message = json.loads(api_result_str)
        
        # --- This part handles the response ---
        # For this guide, we will keep it simple. If the AI wants to use a tool,
        # we would need more logic here. For now, we'll just return its text response.
        final_content = ai_message.get('content', "I'm not sure how to respond.")
        current_conversation.append({"role": "assistant", "content": final_content})
        reply = {"type": "text", "content": final_content}
        
        return reply, current_conversation

    except Exception as e:
        logger.error(f"Error calling Chatbot API: {e}")
        return {"type": "text", "content": "The AI chatbot is currently unavailable."}, conversation_history
    
def create_fertilizer_plan(user_id, report_id: int = None):
    """
    Handles the entire fertilizer plan creation flow.
    If no report_id is given, it lists the user's reports for selection.
    If a report_id is given, it generates the fertilizer plan for that report.
    """
    # Flow 1: No report ID was provided, so we must list the reports for the user to choose.
    if report_id is None:
        reports_data, _ = database.get_user_reports(user_id)
        if not reports_data.get("success") or not reports_data.get("reports"):
            return "You have no saved reports to create a plan from. Please analyze a field first."
        
        formatted_reports = []
        for report in reports_data["reports"][:5]:
            try:
                report_date = report['saved_at'].strftime('%b %d, %Y')
                formatted_reports.append({"report_id": report['id'], "date": report_date})
            except Exception:
                continue
        return formatted_reports # Return a list, which the main handler will turn into buttons.

    # Flow 2: A report ID was provided, so we generate the plan.
    else:
        report_record = database.get_report_by_id(user_id, report_id)
        if not report_record: return f"Sorry, I could not find report #{report_id}."
        
        data = json.loads(report_record['report_data'])
        crop = data.get('recommendations', {}).get('recommended_crops', [None])[0]
        state = data.get('location', {}).get('state')
        soil_type = data.get('soil_analysis', {}).get('prediction')
        
        if not all([crop, state, soil_type]): return f"Report #{report_id} is missing data needed for a plan."
        
        # We explicitly ask for the SHORT advice for the chatbot
        plan = get_fertilizer_plan_for_crop(crop, soil_type, state, short_advice=True)
        
        if plan and plan.get('ai_application_advice'):
            # Return the final, formatted string advice.
            return plan['ai_application_advice']
        else:
            return f"Sorry, I could not generate a fertilizer plan for {crop} in {soil_type} for report #{report_id}."

def get_dashboard_data(user_id, lang='en'): # <-- Add lang
    """
    This is the single source of truth for all dashboard data.
    It fetches the latest report and calculates all necessary metrics in one place.
    """
    report_record = database.get_latest_user_report(user_id)

    if not report_record:
        return {"success": True, "has_data": False}
    
    try:
        report_data = json.loads(report_record['report_data'])
        location = report_data.get('location', {})
        lat, lon = location.get('latitude'), location.get('longitude')
        state, district = location.get('state'), location.get('district')
        top_crop = report_data.get('recommendations', {}).get('recommended_crops', ['N/A'])[0]
        soil_type = report_data.get('soil_analysis', {}).get('prediction', 'N/A')
        
        # --- TRANSLATE DYNAMIC TEXT ---
        if lang == 'hi':
            top_crop_display = CROP_TRANSLATIONS_HI.get(top_crop.lower(), top_crop)
            soil_type_display = SOIL_TRANSLATIONS_HI.get(soil_type.lower(), soil_type)
        else:
            top_crop_display = top_crop
            soil_type_display = soil_type
            
        if not all([lat, lon, state, district]):
             return {"success": False, "error": "Latest report has incomplete location data."}

        username = database.get_username_by_id(user_id)
        current_weather = get_weather_data(lat, lon, lang=lang)
        price_data = get_mandi_prices(state, district, top_crop, lang=lang)
        mandi_price = price_data.get("average_mandi_price")
        price_chart_data = get_dashboard_price_summary(state, district, lang=lang)

        summary = {
            "success": True, 
            "has_data": True, 
            "username": username,
            "location": f"{district.title()}, {state.title()}",
            "current_weather": current_weather,
            # Use the translated display values
            "soil_type": soil_type_display, 
            "last_report": {"date": report_record['saved_at'].strftime('%d-%m-%Y'), "top_crop_recommended": top_crop_display},
            "mandi_price": {"crop": top_crop_display, "price": mandi_price},
            "price_chart": price_chart_data 
        }
        return summary
        
    except Exception as e:
        logger.error(f"Error generating dashboard summary data: {e}", exc_info=True)
        if lang == 'hi':
            return {"success": False, "error": "डैशबोर्ड के लिए रिपोर्ट डेटा पार्स नहीं किया जा सका।"}
        return {"success": False, "error": "Could not parse report data for dashboard."}

def _cache_updater_worker():
    """
    This is the main worker function for our background thread.
    It runs in an infinite loop, waking up periodically to refresh all state caches.
    """
    logger.info("CACHE UPDATER: Background cache refresh thread has started.")
    
    # Get a unique, sorted list of all states from our data
    if not _DISTRICT_TO_STATE_MAP:
        logger.error("CACHE UPDATER: Halting thread because the district-to-state map is not loaded.")
        return
    all_states = sorted(list(set(_DISTRICT_TO_STATE_MAP.values())))
    
    while True:
        logger.info(f"CACHE UPDATER: Starting scheduled refresh for {len(all_states)} states...")
        
        today = datetime.now()
        for state in all_states:
            try:
                # We only try to fetch for today's date during the refresh.
                live_records = _fetch_live_price_data(state, today)
                
                if live_records:
                    # Save the freshly fetched data to the local cache file
                    data_to_cache = {"records": live_records, "timestamp": today.isoformat()}
                    _save_to_local_cache(state, data_to_cache)
                    logger.info(f"CACHE UPDATER: Successfully refreshed cache for '{state}'.")
                else:
                    logger.warning(f"CACHE UPDATER: Could not fetch live data for '{state}'. Its cache was not updated.")
                
                # Small delay to avoid overwhelming the API
                time.sleep(5) 
                
            except Exception as e:
                logger.error(f"CACHE UPDATER: An error occurred for state '{state}' during refresh: {e}")

        sleep_duration_hours = 6
        sleep_duration_seconds = sleep_duration_hours * 3600
        logger.info(f"CACHE UPDATER: All states processed. Sleeping for {sleep_duration_hours} hours.")
        time.sleep(sleep_duration_seconds)


def start_background_cache_updater():
    """
    This function launches the cache updater worker in a single, persistent background thread.
    It should only be called once when the application starts.
    """
    if 'cache_updater_thread' in threading.enumerate():
        logger.info("CACHE UPDATER: Updater thread already running.")
        return

    logger.info("CACHE UPDATER: Initializing and starting background cache refresh thread.")
    thread = threading.Thread(target=_cache_updater_worker, name='cache_updater_thread')
    thread.daemon = True
    thread.start()
