"""
Services module for the attendance system.

Contains background services for notifications, health monitoring, and other automated tasks.
"""

from .notification import NotificationService
from .health import HealthService

__all__ = ["NotificationService", "HealthService"] 