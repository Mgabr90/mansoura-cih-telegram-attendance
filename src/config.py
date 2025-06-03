import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the attendance bot"""
    
    # Bot Configuration
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    
    # Office Location (29R3+7Q El Mansoura 1)
    OFFICE_LATITUDE = float(os.getenv('OFFICE_LATITUDE', 31.0417))
    OFFICE_LONGITUDE = float(os.getenv('OFFICE_LONGITUDE', 31.3778))
    OFFICE_RADIUS = int(os.getenv('OFFICE_RADIUS', 100))
    
    # Database
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'attendance.db')
    
    # Timezone
    TIMEZONE = os.getenv('TIMEZONE', 'Africa/Cairo')
    
    # Notification Settings
    WORK_START_HOUR = int(os.getenv('WORK_START_HOUR', 6))
    WORK_END_HOUR = int(os.getenv('WORK_END_HOUR', 20))
    LATE_THRESHOLD_MINUTES = int(os.getenv('LATE_THRESHOLD_MINUTES', 30))
    MISSED_CHECKOUT_HOURS = int(os.getenv('MISSED_CHECKOUT_HOURS', 10))
    
    # Default Reminder Times
    DEFAULT_CHECKIN_TIME = os.getenv('DEFAULT_CHECKIN_TIME', '09:00')
    DEFAULT_CHECKOUT_TIME = os.getenv('DEFAULT_CHECKOUT_TIME', '17:00')
    
    # Alert Schedule
    LATE_ALERT_START_HOUR = int(os.getenv('LATE_ALERT_START_HOUR', 9))
    LATE_ALERT_END_HOUR = int(os.getenv('LATE_ALERT_END_HOUR', 12))
    MISSED_CHECKOUT_ALERT_HOUR = int(os.getenv('MISSED_CHECKOUT_ALERT_HOUR', 20))
    
    @classmethod
    def validate(cls):
        """Validate configuration settings"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN is required")
        
        if cls.OFFICE_LATITUDE < -90 or cls.OFFICE_LATITUDE > 90:
            errors.append("OFFICE_LATITUDE must be between -90 and 90")
            
        if cls.OFFICE_LONGITUDE < -180 or cls.OFFICE_LONGITUDE > 180:
            errors.append("OFFICE_LONGITUDE must be between -180 and 180")
            
        if cls.OFFICE_RADIUS < 1:
            errors.append("OFFICE_RADIUS must be positive")
        
        return errors

# Validate configuration on import
config_errors = Config.validate()
if config_errors:
    raise ValueError(f"Configuration errors: {', '.join(config_errors)}") 