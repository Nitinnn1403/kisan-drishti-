# database.py - FINAL, CORRECTED VERSION FOR POSTGRESQL

import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import DictCursor
import bcrypt
import logging
import datetime
import json

DATABASE_URL = os.getenv('DATABASE_URL')
logger = logging.getLogger(__name__)

pg_pool = None

def init_connection_pool():
    global pg_pool
    if not DATABASE_URL:
        logger.critical("DATABASE_URL environment variable not set. Application cannot start.")
        return
    try:
        pg_pool = psycopg2.pool.SimpleConnectionPool(1, 5, dsn=DATABASE_URL)
        logger.info("PostgreSQL connection pool created successfully.")
    except Exception as e:
        logger.error(f"Error creating PostgreSQL pool: {e}")

def get_db_connection():
    if not pg_pool:
        logger.error("Database pool is not initialized.")
        return None
    return pg_pool.getconn()

def release_db_connection(conn):
    if pg_pool and conn:
        pg_pool.putconn(conn)

def create_tables():
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            logger.error("Could not get DB connection to create tables.")
            return
        with conn.cursor() as cursor:
            # PostgreSQL uses SERIAL for auto-incrementing IDs and JSONB for JSON data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    contact VARCHAR(20),
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS field_reports (
                    id SERIAL PRIMARY KEY,
                    user_id INT NOT NULL,
                    latitude DECIMAL(10, 8) NOT NULL,
                    longitude DECIMAL(11, 8) NOT NULL,
                    report_data JSONB NOT NULL,
                    saved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
            """)
        conn.commit()
        logger.info("Database tables checked/created successfully for PostgreSQL.")
    except Exception as e:
        logger.error(f"Error creating PostgreSQL tables: {e}")
    finally:
        if conn:
            release_db_connection(conn)

def register_user(username, contact, email, password): # Added all new arguments
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Check if username or email already exists
            cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s", (username, email,))
            if cursor.fetchone():
                return {"success": False, "error": "Username or email already taken."}, 409

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            # Insert all the new fields into the database
            cursor.execute(
                "INSERT INTO users (username, contact, email, password_hash) VALUES (%s, %s, %s, %s) RETURNING id, username",
                (username, contact, email, hashed_password)
            )
            user = cursor.fetchone()
        conn.commit()
        logger.info(f"User '{user['username']}' registered successfully with ID: {user['id']}.")
        # Return the username for the session
        return {"success": True, "message": "Registration successful!", "user_id": user['id'], "username": user['username']}, 201
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return {"success": False, "error": "Database error during registration."}, 500
    finally:
        if conn:
            release_db_connection(conn)

def login_user(email, password): # Changed argument
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            # Select by email
            cursor.execute("SELECT id, full_name, password_hash FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                logger.info(f"User {user['full_name']} logged in successfully.")
                # Return full_name instead of username
                return {"success": True, "user_id": user['id'], "full_name": user['full_name']}, 200
        return {"success": False, "error": "Invalid email or password."}, 401
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return {"success": False, "error": "Database error during login."}, 500
    finally:
        if conn:
            release_db_connection(conn)

def save_report_to_db(user_id, latitude, longitude, report_data_json):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "INSERT INTO field_reports (user_id, latitude, longitude, report_data) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (user_id, latitude, longitude, report_data_json))
        conn.commit()
        logger.info(f"Report saved successfully for user {user_id}.")
        return {"success": True, "message": "Report saved successfully!"}, 201
    except Exception as e:
        logger.error(f"Error saving report to PostgreSQL: {e}")
        return {"success": False, "error": "Database error while saving report."}, 500
    finally:
        if conn:
            release_db_connection(conn)

def get_user_reports(user_id):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            sql = "SELECT id, latitude, longitude, report_data, saved_at FROM field_reports WHERE user_id = %s ORDER BY saved_at DESC"
            cursor.execute(sql, (user_id,))
            reports = [dict(row) for row in cursor.fetchall()]
        logger.info(f"Fetched {len(reports)} reports for user {user_id}.")
        return {"success": True, "reports": reports}, 200
    except Exception as e:
        logger.error(f"Error fetching reports from PostgreSQL: {e}")
        return {"success": False, "error": "Database error while fetching reports."}, 500
    finally:
        if conn:
            release_db_connection(conn)

def get_latest_user_report(user_id):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            sql = "SELECT report_data, saved_at FROM field_reports WHERE user_id = %s ORDER BY saved_at DESC LIMIT 1"
            cursor.execute(sql, (user_id,))
            report = cursor.fetchone()
        return report
    except Exception as e:
        logger.error(f"Error fetching latest report: {e}")
        return None
    finally:
        if conn:
            release_db_connection(conn)

def delete_report_from_db(report_id, user_id):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "DELETE FROM field_reports WHERE id = %s AND user_id = %s"
            cursor.execute(sql, (report_id, user_id))
            rows_affected = cursor.rowcount
        conn.commit()
        if rows_affected > 0:
            logger.info(f"Report ID {report_id} deleted by user {user_id}.")
            return {"success": True, "message": "Report deleted successfully!"}, 200
        else:
            logger.warning(f"Failed delete attempt for report {report_id} by user {user_id}.")
            return {"success": False, "error": "Report not found or permission denied."}, 404
    except Exception as e:
        logger.error(f"Error deleting report from PostgreSQL: {e}")
        return {"success": False, "error": "Database error while deleting report."}, 500
    finally:
        if conn:
            release_db_connection(conn)

def get_report_by_id(user_id, report_id):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            sql = "SELECT id, report_data, saved_at FROM field_reports WHERE user_id = %s AND id = %s"
            cursor.execute(sql, (user_id, report_id))
            report = cursor.fetchone()
        return report
    except Exception as e:
        logger.error(f"Error fetching single report by ID: {e}")
        return None
    finally:
        if conn:
            release_db_connection(conn)

def update_user_password(user_id, current_password, new_password):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            sql_fetch = "SELECT password_hash FROM users WHERE id = %s"
            cursor.execute(sql_fetch, (user_id,))
            user = cursor.fetchone()

            if not user:
                return {"success": False, "error": "User not found."}, 404
            if not bcrypt.checkpw(current_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                return {"success": False, "error": "Incorrect current password."}, 403

            new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            sql_update = "UPDATE users SET password_hash = %s WHERE id = %s"
            cursor.execute(sql_update, (new_hashed_password, user_id))
        conn.commit()
        logger.info(f"Password updated successfully for user ID: {user_id}.")
        return {"success": True, "message": "Password updated successfully!"}, 200
    except Exception as e:
        logger.error(f"Error updating password in PostgreSQL: {e}")
        return {"success": False, "error": "Database error while updating password."}, 500
    finally:
        if conn:
            release_db_connection(conn)

def delete_user_account(user_id):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "DELETE FROM users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            rows_affected = cursor.rowcount
        conn.commit()
        if rows_affected > 0:
            logger.info(f"User account with ID {user_id} has been permanently deleted.")
            return {"success": True, "message": "Account deleted successfully."}, 200
        else:
            logger.warning(f"Attempted to delete a non-existent user with ID {user_id}.")
            return {"success": False, "error": "User not found."}, 404
    except Exception as e:
        logger.error(f"Error deleting user account from PostgreSQL: {e}")
        return {"success": False, "error": "Database error while deleting account."}, 500
    finally:
        if conn:
            release_db_connection(conn)

def get_username_by_id(user_id):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
        return result[0] if result else "User"
    except Exception as e:
        logger.error(f"Error fetching username by ID: {e}")
        return "User"
    finally:
        if conn:
            release_db_connection(conn)