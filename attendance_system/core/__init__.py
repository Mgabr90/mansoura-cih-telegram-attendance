"""
Core modules for the attendance system.

Contains configuration, database, and other fundamental components.
"""

from .config import Config
from .database import AttendanceDatabase

__all__ = ["Config", "AttendanceDatabase"] 