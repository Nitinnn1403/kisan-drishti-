# config.py - Final Configuration for Full Integration

import os
import json
from dotenv import load_dotenv

load_dotenv()

# --- Core App Config ---
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'nitin1403')

# --- API Keys ---
DATA_GOV_IN_API_KEY = os.getenv('DATA_GOV_IN_API_KEY')
OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')
LOCAL_AI_API_URL = os.getenv('LOCAL_AI_API_URL')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# --- Database Config ---
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DB = os.getenv('MYSQL_DB', 'kisan_drishti_db')

# --- ML Model Paths (from .env) ---
PLANT_HEALTH_MODEL_PATH = os.getenv('PLANT_HEALTH_MODEL_PATH')
PLANT_HEALTH_LABELS_PATH = os.getenv('PLANT_HEALTH_LABELS_PATH')
SOIL_TYPE_MODEL_PATH = os.getenv('SOIL_TYPE_MODEL_PATH')
SOIL_TYPE_LABELS_PATH = os.getenv('SOIL_TYPE_LABELS_PATH')

# --- Data File Paths ---
RECOMMEND_DATA_PATH = os.getenv('RECOMMEND_DATA_PATH', 'data/recommend.csv')
MACRO_NUTRIENT_DATA_PATH = os.getenv('MACRO_NUTRIENT_DATA_PATH', 'data/macro.csv')
MICRO_NUTRIENT_DATA_PATH = os.getenv('MICRO_NUTRIENT_DATA_PATH', 'data/micro.csv')
ICRISAT_DATA_PATH = os.getenv('ICRISAT_DATA_PATH', 'data/icrisat_data.csv')
FARM_HARVEST_PRICE_DATA_PATH = os.getenv('FARM_HARVEST_PRICE_DATA_PATH', 'data/FarmHarvestPrice.csv')
RAINFALL_DATA_PATH = os.getenv('RAINFALL_DATA_PATH', 'data/Rainfall_data_Monthly.csv')
MANDI_PRICE_DATA_PATH = os.getenv('MANDI_PRICE_DATA_PATH')

def load_labels(path):
    if not path or not os.path.exists(path): return {}
    try:
        with open(path, 'r') as f:
            return {int(k): v for k, v in json.load(f).items()}
    except Exception as e:
        print(f"ERROR loading labels from '{path}': {e}")
        return {}

PLANT_HEALTH_CLASS_LABELS = load_labels(PLANT_HEALTH_LABELS_PATH)
SOIL_TYPE_CLASS_LABELS = load_labels(SOIL_TYPE_LABELS_PATH)