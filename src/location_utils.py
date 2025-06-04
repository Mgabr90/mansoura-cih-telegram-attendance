import math
from geopy.distance import geodesic

def calculate_distance(user_lat, user_lon, office_lat, office_lon):
    """
    Calculate the distance between two points on Earth using geodesic distance
    Returns distance in meters
    """
    point1 = (user_lat, user_lon)
    point2 = (office_lat, office_lon)
    distance = geodesic(point1, point2).meters
    return distance

def is_within_radius(user_lat, user_lon, office_lat, office_lon, radius_meters):
    """
    Check if user location is within the specified radius of office location
    """
    distance = calculate_distance(user_lat, user_lon, office_lat, office_lon)
    return distance <= radius_meters, distance

def verify_location_with_warnings(user_lat, user_lon, office_lat, office_lon, office_radius, warning_radius=500):
    """
    Verify location with different levels: within radius, warning zone, or outside
    Returns: (status, distance, message)
    Status: 'within' | 'warning' | 'outside'
    """
    distance = calculate_distance(user_lat, user_lon, office_lat, office_lon)
    
    if distance <= office_radius:
        return 'within', distance, f"✅ Location verified: {distance:.0f}m from office"
    elif distance <= warning_radius:
        return 'warning', distance, f"⚠️ You are {distance:.0f}m from office (outside {office_radius}m radius). Attendance recorded with location note."
    else:
        return 'outside', distance, f"🚨 You are {distance:.0f}m from office. This is quite far from the workplace. Attendance recorded with location note."

def get_location_status_emoji(status):
    """Get emoji for location status"""
    if status == 'within':
        return '🟢'
    elif status == 'warning':
        return '🟡'
    else:
        return '🔴'

def plus_code_to_coordinates(plus_code):
    """
    Convert Plus Code to approximate coordinates
    29R3+7Q El Mansoura 1 approximately corresponds to:
    Latitude: 31.0417, Longitude: 31.3778
    """
    # This is a simplified conversion - in production, you might want to use
    # the official Open Location Code library
    if plus_code == "29R3+7Q":
        return 31.0417, 31.3778
    return None, None

def format_location_message(latitude, longitude, address=None):
    """
    Format location information for display
    """
    if address:
        return f"📍 Location: {address}\n🌐 Coordinates: {latitude:.6f}, {longitude:.6f}"
    else:
        return f"🌐 Coordinates: {latitude:.6f}, {longitude:.6f}"

def validate_coordinates(latitude, longitude):
    """
    Validate if coordinates are within valid ranges
    """
    if not (-90 <= latitude <= 90):
        return False, "Invalid latitude: must be between -90 and 90"
    if not (-180 <= longitude <= 180):
        return False, "Invalid longitude: must be between -180 and 180"
    return True, "Valid coordinates" 