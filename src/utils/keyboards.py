from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup

class Keyboards:
    """Reusable keyboard layouts for the attendance bot"""
    
    @staticmethod
    def get_main_keyboard(is_checked_in=False):
        """Get the main keyboard based on check-in status"""
        if is_checked_in:
            keyboard = [
                [KeyboardButton("🔴 Check Out", request_location=True)],
                [KeyboardButton("📊 My Status"), KeyboardButton("📈 My Report")],
                [KeyboardButton("⏰ Reminders"), KeyboardButton("ℹ️ Help")]
            ]
        else:
            keyboard = [
                [KeyboardButton("🟢 Check In", request_location=True)],
                [KeyboardButton("📊 My Status"), KeyboardButton("📈 My Report")],
                [KeyboardButton("⏰ Reminders"), KeyboardButton("ℹ️ Help")]
            ]
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    @staticmethod
    def get_registration_keyboard():
        """Get registration keyboard for new users"""
        keyboard = [[KeyboardButton("📝 Register", request_contact=True)]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    @staticmethod
    def get_contact_sharing_keyboard():
        """Get contact sharing keyboard"""
        keyboard = [[KeyboardButton("📝 Share Contact", request_contact=True)]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    @staticmethod
    def get_admin_panel_keyboard():
        """Get admin panel inline keyboard"""
        keyboard = [
            [InlineKeyboardButton("📊 Today's Report", callback_data="admin_today_report")],
            [InlineKeyboardButton("📈 All Employees Report", callback_data="admin_all_report")],
            [InlineKeyboardButton("📁 Export Data", callback_data="admin_export_menu")],
            [InlineKeyboardButton("👥 Employee List", callback_data="admin_employee_list")],
            [InlineKeyboardButton("🚨 Alert Settings", callback_data="admin_alert_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_export_menu_keyboard():
        """Get export menu inline keyboard"""
        keyboard = [
            [InlineKeyboardButton("📊 Daily CSV", callback_data="export_daily_today")],
            [InlineKeyboardButton("📈 Monthly CSV", callback_data="export_monthly_current")],
            [InlineKeyboardButton("👥 Employee List CSV", callback_data="export_employees_list")],
            [InlineKeyboardButton("📁 Full Attendance CSV", callback_data="export_attendance_30days")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_reminder_settings_keyboard():
        """Get reminder settings inline keyboard"""
        keyboard = [
            [InlineKeyboardButton("⏰ Set Check-in Reminder", callback_data="set_checkin_reminder")],
            [InlineKeyboardButton("🔔 Set Check-out Reminder", callback_data="set_checkout_reminder")],
            [InlineKeyboardButton("🔇 Disable Reminders", callback_data="disable_reminders")],
            [InlineKeyboardButton("📊 View Settings", callback_data="view_reminder_settings")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def get_admin_alerts_keyboard(alert_enabled):
        """Get admin alerts inline keyboard"""
        keyboard = [
            [InlineKeyboardButton(
                "🔇 Disable Alerts" if alert_enabled else "🔔 Enable Alerts", 
                callback_data="toggle_admin_alerts"
            )],
            [InlineKeyboardButton("⏱️ Set Late Threshold", callback_data="set_late_threshold")],
            [InlineKeyboardButton("📊 Test Alert", callback_data="test_admin_alert")]
        ]
        return InlineKeyboardMarkup(keyboard) 