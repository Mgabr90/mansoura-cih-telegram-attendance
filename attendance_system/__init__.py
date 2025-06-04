"""
Enhanced Mansoura CIH Telegram Attendance System

A comprehensive attendance tracking system with enhanced security features,
location-only check-ins, exceptional hours support, and admin management.

Author: Assistant
Version: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "Assistant"
__description__ = "Enhanced Telegram Attendance System for Mansoura CIH"

from .core.config import Config
from .core.database import AttendanceDatabase
from .main import AttendanceBot

__all__ = ["Config", "AttendanceDatabase", "AttendanceBot"] 