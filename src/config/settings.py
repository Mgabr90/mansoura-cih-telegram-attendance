import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Office Location Configuration
OFFICE_LATITUDE = float(os.getenv('OFFICE_LATITUDE', 31.0417))
OFFICE_LONGITUDE = float(os.getenv('OFFICE_LONGITUDE', 31.3778))
OFFICE_RADIUS = int(os.getenv('OFFICE_RADIUS', 100))

# Database Configuration
DATABASE_NAME = os.getenv('DATABASE_NAME', 'attendance.db')

# Timezone Configuration
TIMEZONE = os.getenv('TIMEZONE', 'Africa/Cairo')

# Notification Settings
NOTIFICATION_WORK_START = 6  # 6 AM
NOTIFICATION_WORK_END = 20   # 8 PM
LATE_ALERT_INTERVAL = 30     # Minutes
MISSED_CHECKOUT_THRESHOLD = 10  # Hours

# Default Reminder Times
DEFAULT_CHECKIN_TIME = '09:00'
DEFAULT_CHECKOUT_TIME = '17:00'

# Admin Settings
DEFAULT_LATE_THRESHOLD = 30  # Minutes

# Export Settings
DEFAULT_EXPORT_DAYS = 30

# Validate required settings
def validate_settings():
    """Validate that all required settings are present"""
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required but not set in environment variables")
    
    if not (-90 <= OFFICE_LATITUDE <= 90):
        raise ValueError(f"Invalid OFFICE_LATITUDE: {OFFICE_LATITUDE}")
    
    if not (-180 <= OFFICE_LONGITUDE <= 180):
        raise ValueError(f"Invalid OFFICE_LONGITUDE: {OFFICE_LONGITUDE}")
    
    if OFFICE_RADIUS <= 0:
        raise ValueError(f"OFFICE_RADIUS must be positive: {OFFICE_RADIUS}")
    
    return True 