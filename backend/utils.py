# utils.py - Contains general utility functions
import logging

logger = logging.getLogger(__name__)

def get_indian_state_from_gps(latitude, longitude):
    """ Determines the approximate Indian state based on GPS coordinates. """
    state_bounds = {
        "ANDHRA PRADESH": {"lat_min": 12.5, "lat_max": 19.5, "lon_min": 76.5, "lon_max": 84.5},
        "GUJARAT": {"lat_min": 20.0, "lat_max": 25.0, "lon_min": 68.0, "lon_max": 74.5},
        "HARYANA": {"lat_min": 27.5, "lat_max": 31.0, "lon_min": 74.0, "lon_max": 77.5},
        "HIMACHAL PRADESH": {"lat_min": 30.0, "lat_max": 33.5, "lon_min": 75.5, "lon_max": 79.0},
        "KARNATAKA": {"lat_min": 11.5, "lat_max": 19.0, "lon_min": 74.0, "lon_max": 78.5},
        "KERALA": {"lat_min": 8.0, "lat_max": 12.5, "lon_min": 74.5, "lon_max": 77.5},
        "MADHYA PRADESH": {"lat_min": 21.0, "lat_max": 27.0, "lon_min": 74.0, "lon_max": 83.0},
        "MAHARASHTRA": {"lat_min": 15.5, "lat_max": 22.5, "lon_min": 72.5, "lon_max": 81.0},
        "PUNJAB": {"lat_min": 29.0, "lat_max": 32.5, "lon_min": 73.5, "lon_max": 76.5},
        "RAJASTHAN": {"lat_min": 23.0, "lat_max": 30.5, "lon_min": 69.5, "lon_max": 78.5},
        "TAMIL NADU": {"lat_min": 8.0, "lat_max": 13.5, "lon_min": 76.5, "lon_max": 80.5},
        "TELANGANA": {"lat_min": 15.8, "lat_max": 19.5, "lon_min": 77.0, "lon_max": 81.5},
        "UTTAR PRADESH": {"lat_min": 23.5, "lat_max": 31.0, "lon_min": 77.0, "lon_max": 84.5},
        "WEST BENGAL": {"lat_min": 21.5, "lat_max": 27.5, "lon_min": 86.0, "lon_max": 89.5},
    }
    for state, bounds in state_bounds.items():
        if (bounds["lat_min"] <= latitude <= bounds["lat_max"] and
            bounds["lon_min"] <= longitude <= bounds["lon_max"]):
            return state
    return "UNKNOWN"

def get_district_from_gps(latitude, longitude):
    """ This is a simplified placeholder. A real app would use a reverse geocoding API. """
    district_data = {
        "AHMADABAD": {"lat": 23.0225, "lon": 72.5714}, "SURAT": {"lat": 21.1702, "lon": 72.8311},
        "PUNE": {"lat": 18.5204, "lon": 73.8567}, "BENGALURU URBAN": {"lat": 12.9716, "lon": 77.5946}
    }
    closest_district, min_dist = "Unknown", float('inf')
    for district, coords in district_data.items():
        dist = (latitude - coords['lat'])**2 + (longitude - coords['lon'])**2
        if dist < min_dist:
            min_dist, closest_district = dist, district
    return closest_district