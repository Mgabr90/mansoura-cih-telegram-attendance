from datetime import datetime
import pytz
from config.settings import OFFICE_RADIUS

class Messages:
    """Standardized messages for the attendance bot"""
    
    @staticmethod
    def welcome_new_user(first_name):
        """Welcome message for new users"""
        return (
            f"👋 Welcome to El Mansoura Attendance System!\n\n"
            f"Hello {first_name}! You need to register first to use this bot.\n"
            f"Please click the 'Register' button below to share your contact information."
        )
    
    @staticmethod
    def welcome_back(first_name):
        """Welcome back message for registered users"""
        return (
            f"👋 Welcome back, {first_name}!\n\n"
            f"🏢 Office Location: El Mansoura (29R3+7Q)\n"
            f"📏 Attendance Radius: {OFFICE_RADIUS}m\n\n"
            f"Use the buttons below to check in/out or view your status."
        )
    
    @staticmethod
    def registration_request():
        """Registration request message"""
        return (
            "📝 **Employee Registration**\n\n"
            "Please share your contact information to complete registration."
        )
    
    @staticmethod
    def registration_success(user, phone_number):
        """Registration success message"""
        return (
            f"✅ **Registration Successful!**\n\n"
            f"👤 Name: {user.first_name} {user.last_name or ''}\n"
            f"📱 Phone: {phone_number}\n"
            f"🆔 Username: @{user.username or 'N/A'}\n\n"
            f"You can now use the attendance system!"
        )
    
    @staticmethod
    def location_error(distance):
        """Location error message when too far from office"""
        return (
            f"❌ **Location Error**\n\n"
            f"You are {distance:.0f}m away from the office.\n"
            f"Please move closer to the office (within {OFFICE_RADIUS}m radius).\n\n"
            f"🏢 Office Location: 29R3+7Q El Mansoura 1"
        )
    
    @staticmethod
    def checkin_success(time_str, distance, latitude, longitude):
        """Check-in success message"""
        return (
            f"✅ **Check-In Successful!**\n\n"
            f"⏰ Time: {time_str}\n"
            f"📍 Distance from office: {distance:.0f}m\n"
            f"🌐 Location: {latitude:.6f}, {longitude:.6f}"
        )
    
    @staticmethod
    def checkout_success(time_str, work_duration, distance, latitude, longitude):
        """Check-out success message"""
        hours, remainder = divmod(work_duration.total_seconds(), 3600)
        minutes = remainder // 60
        
        return (
            f"✅ **Check-Out Successful!**\n\n"
            f"⏰ Time: {time_str}\n"
            f"⏱️ Work Duration: {int(hours)}h {int(minutes)}m\n"
            f"📍 Distance from office: {distance:.0f}m\n"
            f"🌐 Location: {latitude:.6f}, {longitude:.6f}"
        )
    
    @staticmethod
    def attendance_status_not_checked_in():
        """Status message when not checked in"""
        egypt_tz = pytz.timezone(Config.TIMEZONE)
        today = datetime.now(egypt_tz).date().strftime('%Y-%m-%d')
        
        return (
            f"📊 **Attendance Status - {today}**\n\n"
            f"❌ Not checked in today\n"
            f"💡 Use the 'Check In' button to record your attendance"
        )
    
    @staticmethod
    def attendance_status(status_data):
        """Format attendance status message"""
        check_in_time = datetime.fromisoformat(status_data[0]) if status_data[0] else None
        check_out_time = datetime.fromisoformat(status_data[1]) if status_data[1] else None
        status = status_data[2]
        
        egypt_tz = pytz.timezone(Config.TIMEZONE)
        today = datetime.now(egypt_tz).date().strftime('%Y-%m-%d')
        
        status_text = f"📊 **Attendance Status - {today}**\n\n"
        
        if check_in_time:
            status_text += f"🟢 Check-in: {check_in_time.strftime('%H:%M:%S')}\n"
        
        if check_out_time:
            status_text += f"🔴 Check-out: {check_out_time.strftime('%H:%M:%S')}\n"
            work_duration = check_out_time - check_in_time
            hours, remainder = divmod(work_duration.total_seconds(), 3600)
            minutes = remainder // 60
            status_text += f"⏱️ Work Duration: {int(hours)}h {int(minutes)}m\n"
        else:
            if check_in_time:
                current_time = datetime.now(egypt_tz)
                work_duration = current_time - check_in_time
                hours, remainder = divmod(work_duration.total_seconds(), 3600)
                minutes = remainder // 60
                status_text += f"⏱️ Currently working: {int(hours)}h {int(minutes)}m\n"
        
        status_text += f"\n📈 Status: {status.replace('_', ' ').title()}"
        return status_text
    
    @staticmethod
    def help_text(is_admin=False):
        """Generate help text based on user role"""
        help_text = """
🤖 **El Mansoura Attendance Bot Help**

**Available Commands:**
• `/start` - Start the bot and see main menu
• `/register` - Register as an employee
• `/status` - Check your current attendance status
• `/report` - Get your attendance report (last 7 days)
• `/help` - Show this help message

**Reminder Commands:**
• `/reminders` - Manage attendance reminders
• `/set_reminder checkin HH:MM` - Set check-in reminder
• `/set_reminder checkout HH:MM` - Set check-out reminder

**How to Use:**
1. 📝 Register first by sharing your contact
2. 🟢 **Check In**: Press "Check In" and share your location
3. 🔴 **Check Out**: Press "Check Out" and share your location
4. 📊 View your status and reports anytime

**Location Requirements:**
• You must be within 100 meters of the office
• Office Location: 29R3+7Q El Mansoura 1
• GPS must be enabled on your device"""

        if is_admin:
            help_text += """

**Admin Commands:**
• `/admin` - View admin panel
• `/add_admin [user_id]` - Add new admin
• `/all_report` - Get all employees report
• `/admin_alerts` - Manage admin alert settings

**Export Commands:**
• `/export_daily [YYYY-MM-DD]` - Export daily report (CSV)
• `/export_monthly [YYYY] [MM]` - Export monthly summary (CSV)
• `/export_employees` - Export employee list (CSV)
• `/export_attendance [start] [end]` - Export detailed data (CSV)"""

        help_text += """

**Notes:**
• All times are in Cairo timezone
• You can only check in/out once per day
• Location sharing is required for attendance
        """
        return help_text
    
    @staticmethod
    def admin_panel():
        """Admin panel message"""
        return "🔧 **Admin Panel**\n\nSelect an option:"
    
    @staticmethod
    def export_menu():
        """Export menu message"""
        return "📁 **Export Data Menu**\n\nChoose export type:"
    
    @staticmethod
    def reminder_settings():
        """Reminder settings message"""
        return "⏰ **Reminder Settings**\n\nManage your attendance reminders:"
    
    @staticmethod
    def admin_alerts_info(alert_enabled, late_threshold):
        """Admin alerts information message"""
        status = "Enabled" if alert_enabled else "Disabled"
        return (
            f"🚨 **Admin Alert Settings**\n\n"
            f"Status: {status}\n"
            f"Late Threshold: {late_threshold} minutes\n\n"
            f"You will receive alerts for:\n"
            f"• Late check-ins\n"
            f"• Missed check-outs\n"
            f"• Attendance violations"
        )
    
    @staticmethod
    def checkin_reminder(first_name, reminder_time):
        """Check-in reminder message"""
        return f"""
🔔 **Check-in Reminder**

Good morning {first_name}! 

⏰ It's {reminder_time} - time to check in to the office.
📍 Remember to be within {OFFICE_RADIUS}m of El Mansoura office location.

Tap the button below to check in:
        """
    
    @staticmethod
    def checkout_reminder(first_name, checkout_time):
        """Check-out reminder message"""
        return f"""
🔔 **Check-out Reminder**

Hi {first_name}! 

⏰ It's {checkout_time} - don't forget to check out.
📊 Make sure to record your departure time.

Tap the button below to check out:
        """
    
    @staticmethod
    def late_alert(late_employees, late_threshold):
        """Late check-in alert for admins"""
        egypt_tz = pytz.timezone(Config.TIMEZONE)
        current_time = datetime.now(egypt_tz)
        
        message = f"""
🚨 **Late Check-in Alert**

{len(late_employees)} employee(s) are late for check-in:

"""
        for employee in late_employees:
            telegram_id, first_name, last_name, username, expected_time = employee
            full_name = f"{first_name} {last_name or ''}".strip()
            username_str = f"@{username}" if username else "No username"
            
            # Calculate late minutes
            try:
                expected = datetime.strptime(expected_time, '%H:%M').time()
                current = current_time.time()
                expected_minutes = expected.hour * 60 + expected.minute
                current_minutes = current.hour * 60 + current.minute
                late_minutes = max(0, current_minutes - expected_minutes)
            except:
                late_minutes = 0
            
            message += f"• **{full_name}** ({username_str}) - {late_minutes} minutes late\n"
        
        message += f"\n⏰ Threshold: {late_threshold} minutes\n📅 Date: {current_time.strftime('%Y-%m-%d')}"
        return message
    
    @staticmethod
    def missed_checkout_alert(missed_employees):
        """Missed check-out alert for admins"""
        egypt_tz = pytz.timezone(Config.TIMEZONE)
        current_time = datetime.now(egypt_tz)
        
        message = f"""
⚠️ **Missed Check-out Alert**

{len(missed_employees)} employee(s) forgot to check out:

"""
        for employee in missed_employees:
            telegram_id, first_name, last_name, username, checkin_time = employee
            full_name = f"{first_name} {last_name or ''}".strip()
            username_str = f"@{username}" if username else "No username"
            
            checkin_dt = datetime.fromisoformat(checkin_time)
            hours_worked = (current_time - checkin_dt).total_seconds() / 3600
            
            message += f"• **{full_name}** ({username_str}) - {hours_worked:.1f} hours since check-in\n"
        
        message += f"\n📅 Date: {current_time.strftime('%Y-%m-%d')}"
        return message 