"""
Configuration module for the Enhanced Attendance System.

This module handles all configuration settings including environment variables,
validation, and default values.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """
    Configuration class containing all system settings.
    
    This class loads configuration from environment variables and provides
    validation and default values.
    """
    
    # Bot Configuration
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    
    # Office Location Configuration (29R3+7Q El Mansoura 1)
    OFFICE_LATITUDE: float = float(os.getenv('OFFICE_LATITUDE', '31.0417'))
    OFFICE_LONGITUDE: float = float(os.getenv('OFFICE_LONGITUDE', '31.3778'))
    OFFICE_RADIUS: int = int(os.getenv('OFFICE_RADIUS', '100'))
    OFFICE_ADDRESS: str = os.getenv('OFFICE_ADDRESS', '29R3+7Q El Mansoura 1')
    
    # Database Configuration
    DATABASE_NAME: str = os.getenv('DATABASE_NAME', 'attendance.db')
    
    # Timezone Configuration
    TIMEZONE: str = os.getenv('TIMEZONE', 'Africa/Cairo')
    
    # Work Hours Configuration
    DEFAULT_WORK_START: str = os.getenv('DEFAULT_WORK_START', '09:00')
    DEFAULT_WORK_END: str = os.getenv('DEFAULT_WORK_END', '17:00')
    
    # Notification Configuration
    LATE_THRESHOLD_MINUTES: int = int(os.getenv('LATE_THRESHOLD_MINUTES', '30'))
    MISSED_CHECKOUT_HOURS: int = int(os.getenv('MISSED_CHECKOUT_HOURS', '10'))
    ADMIN_DAILY_SUMMARY_TIME: str = os.getenv('ADMIN_DAILY_SUMMARY_TIME', '20:00')
    
    # Server Configuration
    PORT: int = int(os.getenv('PORT', '8080'))
    SERVER_URL: Optional[str] = os.getenv('SERVER_URL')
    
    # Security Configuration
    LOCATION_ONLY_ATTENDANCE: bool = os.getenv('LOCATION_ONLY_ATTENDANCE', 'true').lower() == 'true'
    MANUAL_ENTRY_DISABLED: bool = os.getenv('MANUAL_ENTRY_DISABLED', 'true').lower() == 'true'
    
    # Wake-up Configuration
    HEALTH_CHECK_INTERVAL: int = int(os.getenv('HEALTH_CHECK_INTERVAL', '14'))
    ENABLE_SERVER_WAKEUP: bool = os.getenv('ENABLE_SERVER_WAKEUP', 'false').lower() == 'true'
    
    # Development Configuration
    DEBUG: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls) -> list[str]:
        """
        Validate configuration settings.
        
        Returns:
            List of validation error messages. Empty if all valid.
        """
        errors = []
        
        # Required fields
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN is required")
        
        # Coordinate validation
        if not (-90 <= cls.OFFICE_LATITUDE <= 90):
            errors.append("OFFICE_LATITUDE must be between -90 and 90")
            
        if not (-180 <= cls.OFFICE_LONGITUDE <= 180):
            errors.append("OFFICE_LONGITUDE must be between -180 and 180")
            
        # Radius validation
        if cls.OFFICE_RADIUS < 1:
            errors.append("OFFICE_RADIUS must be positive")
        
        # Port validation
        if not (1 <= cls.PORT <= 65535):
            errors.append("PORT must be between 1 and 65535")
        
        return errors
    
    @classmethod
    def is_valid(cls) -> bool:
        """Check if configuration is valid."""
        return len(cls.validate()) == 0
    
    @classmethod
    def get_summary(cls) -> dict:
        """Get configuration summary for logging."""
        return {
            'office_location': f"{cls.OFFICE_LATITUDE}, {cls.OFFICE_LONGITUDE}",
            'office_radius': f"{cls.OFFICE_RADIUS}m",
            'timezone': cls.TIMEZONE,
            'work_hours': f"{cls.DEFAULT_WORK_START} - {cls.DEFAULT_WORK_END}",
            'security_enabled': cls.LOCATION_ONLY_ATTENDANCE,
            'debug_mode': cls.DEBUG
        }


# Validate configuration on import
config_errors = Config.validate()
if config_errors:
    raise ValueError(f"Configuration errors: {', '.join(config_errors)}") 