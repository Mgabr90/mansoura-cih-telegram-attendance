"""
Handlers module for the attendance system.

Contains all Telegram bot message and command handlers.
"""

from .employee import EmployeeHandlers
from .admin import AdminHandlers

__all__ = ["EmployeeHandlers", "AdminHandlers"] 