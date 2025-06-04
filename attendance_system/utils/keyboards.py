"""
Keyboard utility module for the Enhanced Attendance System.

This module provides keyboard builders for Telegram bot interactions.
"""

from typing import List, Optional
from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

from ..core.config import Config


class KeyboardBuilder:
    """
    Keyboard builder class for creating Telegram keyboards.
    
    Provides methods to create consistent keyboards throughout the application.
    """
    
    @staticmethod
    def get_location_keyboard(is_checked_in: bool = False) -> ReplyKeyboardMarkup:
        """
        Get location-only keyboard for attendance.
        
        Args:
            is_checked_in: Whether user is currently checked in
            
        Returns:
            ReplyKeyboardMarkup with location sharing buttons
        """
        if is_checked_in:
            keyboard = [
                [KeyboardButton("🔴 Check Out", request_location=True)],
                [KeyboardButton("📊 My Status"), KeyboardButton("📈 My Report")],
                [KeyboardButton("ℹ️ Help")]
            ]
        else:
            keyboard = [
                [KeyboardButton("🟢 Check In", request_location=True)],
                [KeyboardButton("📊 My Status"), KeyboardButton("📈 My Report")],
                [KeyboardButton("ℹ️ Help")]
            ]
        
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=False
        )
    
    @staticmethod
    def get_registration_keyboard() -> ReplyKeyboardMarkup:
        """
        Get registration keyboard for new users.
        
        Returns:
            ReplyKeyboardMarkup with contact sharing button
        """
        keyboard = [[KeyboardButton("📝 Register", request_contact=True)]]
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        )
    
    @staticmethod
    def get_contact_keyboard() -> ReplyKeyboardMarkup:
        """
        Get contact sharing keyboard.
        
        Returns:
            ReplyKeyboardMarkup with contact sharing button
        """
        keyboard = [[KeyboardButton("📱 Share Contact", request_contact=True)]]
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        )
    
    @staticmethod
    def get_admin_main_keyboard() -> InlineKeyboardMarkup:
        """
        Get main admin control panel keyboard.
        
        Returns:
            InlineKeyboardMarkup with admin options
        """
        keyboard = [
            [
                InlineKeyboardButton("📊 Today's Report", callback_data="admin_today_report"),
                InlineKeyboardButton("👥 All Employees", callback_data="admin_all_employees")
            ],
            [
                InlineKeyboardButton("📅 Exceptional Hours", callback_data="admin_exceptional_hours"),
                InlineKeyboardButton("📈 Analytics", callback_data="admin_analytics")
            ],
            [
                InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings"),
                InlineKeyboardButton("🖥️ Server Status", callback_data="admin_server_status")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_admin_settings_keyboard() -> InlineKeyboardMarkup:
        """
        Get admin settings keyboard.
        
        Returns:
            InlineKeyboardMarkup with settings options
        """
        keyboard = [
            [
                InlineKeyboardButton("🔔 Alert Settings", callback_data="admin_alert_settings"),
                InlineKeyboardButton("👨‍💼 Manage Admins", callback_data="admin_manage_admins")
            ],
            [
                InlineKeyboardButton("📊 Report Settings", callback_data="admin_report_settings"),
                InlineKeyboardButton("🔧 System Config", callback_data="admin_system_config")
            ],
            [
                InlineKeyboardButton("« Back to Main", callback_data="admin_main_menu")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_confirmation_keyboard(confirm_data: str, cancel_data: str = "cancel") -> InlineKeyboardMarkup:
        """
        Get confirmation keyboard for actions.
        
        Args:
            confirm_data: Callback data for confirmation
            cancel_data: Callback data for cancellation
            
        Returns:
            InlineKeyboardMarkup with yes/no options
        """
        keyboard = [
            [
                InlineKeyboardButton("✅ Confirm", callback_data=confirm_data),
                InlineKeyboardButton("❌ Cancel", callback_data=cancel_data)
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_pagination_keyboard(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
        """
        Get pagination keyboard for lists.
        
        Args:
            page: Current page number (0-indexed)
            total_pages: Total number of pages
            prefix: Callback data prefix
            
        Returns:
            InlineKeyboardMarkup with pagination controls
        """
        keyboard = []
        
        # Page navigation
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("« Previous", callback_data=f"{prefix}_page_{page-1}"))
        
        nav_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="page_info"))
        
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next »", callback_data=f"{prefix}_page_{page+1}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Back button
        keyboard.append([InlineKeyboardButton("« Back", callback_data=f"{prefix}_back")])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_employee_actions_keyboard(employee_id: int) -> InlineKeyboardMarkup:
        """
        Get employee action keyboard for admin use.
        
        Args:
            employee_id: Employee Telegram ID
            
        Returns:
            InlineKeyboardMarkup with employee management options
        """
        keyboard = [
            [
                InlineKeyboardButton("📊 View Report", callback_data=f"emp_report_{employee_id}"),
                InlineKeyboardButton("📅 Set Exception", callback_data=f"emp_exception_{employee_id}")
            ],
            [
                InlineKeyboardButton("⚙️ Edit Profile", callback_data=f"emp_edit_{employee_id}"),
                InlineKeyboardButton("🔧 Work Hours", callback_data=f"emp_hours_{employee_id}")
            ],
            [
                InlineKeyboardButton("« Back to List", callback_data="admin_all_employees")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_quick_action_keyboard() -> InlineKeyboardMarkup:
        """
        Get quick action keyboard for frequent admin tasks.
        
        Returns:
            InlineKeyboardMarkup with quick actions
        """
        keyboard = [
            [
                InlineKeyboardButton("🔄 Refresh Report", callback_data="admin_refresh"),
                InlineKeyboardButton("📤 Send Summary", callback_data="admin_send_summary")
            ],
            [
                InlineKeyboardButton("📋 Export Data", callback_data="admin_export"),
                InlineKeyboardButton("🧹 Cleanup", callback_data="admin_cleanup")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard) 