# database.py - NEW VERSION FOR POSTGRESQL

import os
import psycopg2
from psycopg2 import pool
from psycopg2.extras import DictCursor
import bcrypt
import logging
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

DATABASE_URL = os.getenv('DATABASE_URL')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
    if not pg_pool: return None
    return pg_pool.getconn()

def release_db_connection(conn):
    if pg_pool and conn:
        pg_pool.putconn(conn)

def create_tables():
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # PostgreSQL uses SERIAL for auto-incrementing IDs and JSONB for JSON data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            # Create 'field_reports' table
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

# --- All functions below are updated for PostgreSQL ---

def register_user(username, password):
    """Registers a new user in the database."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return {"success": False, "error": "Username already exists."}, 409

            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            # Use RETURNING id to get the new user's ID
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
                (username, hashed_password)
            )
            user_id = cursor.fetchone()['id']
        conn.commit()
        user_id = cursor.lastrowid

        logger.info(f"User {username} registered successfully with ID: {user_id}.")
        return {"success": True, "user_id": user_id, "username": username}, 201
    except Exception as e:
        logger.error(f"Error during registration: {e}")
        return {"success": False, "error": "Database error during registration."}, 500
    finally:
        if conn:
            release_db_connection(conn)

def login_user(username, password):
    """Authenticates a user against the database."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("SELECT id, username, password_hash FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                logger.info(f"User {username} logged in successfully.")
                return {"success": True, "user_id": user['id'], "username": user['username']}, 200
        return {"success": False, "error": "Invalid username or password."}, 401
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return {"success": False, "error": "Database error during login."}, 500
    finally:
        if conn:
            release_db_connection(conn)
            