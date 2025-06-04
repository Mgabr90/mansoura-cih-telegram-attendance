"""
Message utility module for the Enhanced Attendance System.

This module provides message formatting and templates for consistent messaging.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import pytz

from ..core.config import Config


class MessageFormatter:
    """
    Message formatter class for creating consistent messages.
    
    Provides templates and formatting methods for various message types.
    """
    
    def __init__(self):
        """Initialize message formatter."""
        self.timezone = pytz.timezone(Config.TIMEZONE)
    
    def format_welcome_message(self, first_name: str, is_registered: bool = False) -> str:
        """
        Format welcome message for users.
        
        Args:
            first_name: User's first name
            is_registered: Whether user is already registered
            
        Returns:
            Formatted welcome message
        """
        if is_registered:
            return f"""
👋 **Welcome back, {first_name}!**

🏢 **Office Location:** {Config.OFFICE_ADDRESS}
📏 **Attendance Radius:** {Config.OFFICE_RADIUS}m

✅ **Security Features:**
🔒 Location sharing is MANDATORY
🚫 Manual location entry is DISABLED

Use the buttons below to check in/out or view your status.
"""
        else:
            return f"""
👋 **Welcome to Enhanced Attendance System!**

Hello {first_name}! You need to register first to use this bot.

📝 Please click the 'Register' button below to share your contact information.

🔒 **Security Notice:** This system uses location-only attendance tracking for enhanced security.
"""
    
    def format_check_in_success(self, time_str: str, distance: float, 
                              is_late: bool = False, late_reason: Optional[str] = None) -> str:
        """
        Format successful check-in message.
        
        Args:
            time_str: Check-in time string
            distance: Distance from office
            is_late: Whether check-in is late
            late_reason: Reason for being late
            
        Returns:
            Formatted check-in message
        """
        message = f"""
✅ **Check-In Successful!**

⏰ **Time:** {time_str}
📍 **Distance from office:** {distance:.0f}m
🌐 **Security:** Location verified
"""
        
        if is_late:
            message += f"\n⏰ **Late Check-in**"
            if late_reason:
                message += f"\n📝 **Reason:** {late_reason}"
        else:
            message += f"\n✨ **On time - Great job!**"
        
        return message
    
    def format_check_out_success(self, time_str: str, distance: float, 
                               work_duration: timedelta, is_early: bool = False, 
                               early_reason: Optional[str] = None) -> str:
        """
        Format successful check-out message.
        
        Args:
            time_str: Check-out time string
            distance: Distance from office
            work_duration: Total work duration
            is_early: Whether check-out is early
            early_reason: Reason for early departure
            
        Returns:
            Formatted check-out message
        """
        hours, remainder = divmod(work_duration.total_seconds(), 3600)
        minutes = remainder // 60
        
        message = f"""
✅ **Check-Out Successful!**

⏰ **Time:** {time_str}
⏱️ **Work Duration:** {int(hours)}h {int(minutes)}m
📍 **Distance from office:** {distance:.0f}m
🌐 **Security:** Location verified
"""
        
        if is_early:
            message += f"\n⏰ **Early Check-out**"
            if early_reason:
                message += f"\n📝 **Reason:** {early_reason}"
        else:
            message += f"\n✨ **Full workday completed!**"
        
        return message
    
    def format_location_denied_message(self, distance: float) -> str:
        """
        Format location verification failed message.
        
        Args:
            distance: Distance from office
            
        Returns:
            Formatted denial message
        """
        return f"""
❌ **Location Verification Failed**

You are {distance:.0f}m away from the office.
Attendance is ONLY allowed within {Config.OFFICE_RADIUS}m of the office.

🏢 **Office Location:** {Config.OFFICE_ADDRESS}
📱 Please move closer and try again.

⚠️ **Security Notice:** Manual location entry is disabled for security.
"""
    
    def format_attendance_status(self, status_data: Dict[str, Any], date_str: str) -> str:
        """
        Format attendance status message.
        
        Args:
            status_data: Attendance status information
            date_str: Date string
            
        Returns:
            Formatted status message
        """
        if not status_data:
            return f"""
📊 **Attendance Status - {date_str}**

❌ Not checked in today
⏰ Work Hours: {Config.DEFAULT_WORK_START} - {Config.DEFAULT_WORK_END}
💡 Use the 'Check In' button to record your attendance
"""
        
        check_in_time = status_data.get('check_in_time')
        check_out_time = status_data.get('check_out_time')
        is_late = status_data.get('is_late', False)
        is_early = status_data.get('is_early_checkout', False)
        
        message = f"📊 **Attendance Status - {date_str}**\n\n"
        
        if check_in_time:
            check_in_dt = datetime.fromisoformat(check_in_time)
            message += f"✅ Checked in: {check_in_dt.strftime('%H:%M:%S')}"
            if is_late:
                message += " (⏰ Late)"
            message += "\n"
        
        if check_out_time:
            check_out_dt = datetime.fromisoformat(check_out_time)
            message += f"✅ Checked out: {check_out_dt.strftime('%H:%M:%S')}"
            if is_early:
                message += " (⏰ Early)"
            message += "\n"
            
            # Calculate duration
            if check_in_time:
                duration = check_out_dt - check_in_dt
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes = remainder // 60
                message += f"⏱️ Work duration: {int(hours)}h {int(minutes)}m"
        elif check_in_time:
            current_time = datetime.now(self.timezone)
            check_in_dt = datetime.fromisoformat(check_in_time)
            duration = current_time - check_in_dt
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes = remainder // 60
            message += f"⏳ Currently working\n"
            message += f"⏱️ Duration so far: {int(hours)}h {int(minutes)}m"
        
        return message
    
    def format_daily_summary(self, summary_data: Dict[str, Any]) -> str:
        """
        Format daily attendance summary for admins.
        
        Args:
            summary_data: Daily summary statistics
            
        Returns:
            Formatted summary message
        """
        date = summary_data.get('date', 'Today')
        total_employees = summary_data.get('total_employees', 0)
        checked_in = summary_data.get('checked_in', 0)
        checked_out = summary_data.get('checked_out', 0)
        late_checkins = summary_data.get('late_checkins', 0)
        early_checkouts = summary_data.get('early_checkouts', 0)
        attendance_rate = summary_data.get('attendance_rate', 0)
        
        message = f"""
📊 **Daily Attendance Summary - {date}**

👥 **Overview:**
• Total Employees: {total_employees}
• Checked In Today: {checked_in}
• Checked Out Today: {checked_out}
• Still Working: {checked_in - checked_out}

⏰ **Issues:**
• Late Check-ins: {late_checkins}
• Early Check-outs: {early_checkouts}

📈 **Attendance Rate: {attendance_rate:.1f}%**
"""
        
        # Add late employees if any
        late_employees = summary_data.get('late_employees', [])
        if late_employees:
            message += "\n🕐 **Late Arrivals:**\n"
            for emp in late_employees:
                name = f"{emp[0]} {emp[1] or ''}".strip()
                check_in_time = datetime.fromisoformat(emp[2]).strftime('%H:%M')
                reason = emp[3] if emp[3] else "No reason provided"
                message += f"• {name} - {check_in_time} ({reason})\n"
        
        # Add early checkouts if any
        early_employees = summary_data.get('early_employees', [])
        if early_employees:
            message += "\n🕕 **Early Departures:**\n"
            for emp in early_employees:
                name = f"{emp[0]} {emp[1] or ''}".strip()
                check_out_time = datetime.fromisoformat(emp[2]).strftime('%H:%M')
                reason = emp[3] if emp[3] else "No reason provided"
                message += f"• {name} - {check_out_time} ({reason})\n"
        
        # Add timestamp
        current_time = datetime.now(self.timezone)
        message += f"\n🕘 Report generated at {current_time.strftime('%H:%M:%S')}"
        
        return message
    
    def format_help_message(self, is_admin: bool = False, is_registered: bool = True) -> str:
        """
        Format comprehensive help message.
        
        Args:
            is_admin: Whether user is admin
            is_registered: Whether user is registered
            
        Returns:
            Formatted help message
        """
        message = """
🤖 **Enhanced Attendance System**

**🔒 Security Features:**
📍 Location sharing is MANDATORY
🚫 Manual location entry is DISABLED
✅ Must be within 100m of office location

**👤 Employee Commands:**
"""
        
        if not is_registered:
            message += """
📝 `/register` - Register as an employee
⚠️ You must register before using the system
"""
        else:
            message += """
📊 Use buttons to check status and reports
🟢 Use "Check In" button with location
🔴 Use "Check Out" button with location
📝 Late check-ins require a reason
📝 Early check-outs require a reason
"""
        
        message += f"""
🆔 `/myid` - Get your Telegram user ID
ℹ️ `/help` - Show this help message

**⏰ Working Hours:**
🏢 Standard: {Config.DEFAULT_WORK_START} - {Config.DEFAULT_WORK_END}
📅 Exceptional hours may apply for specific dates

**📍 Office Location:**
🏢 {Config.OFFICE_ADDRESS}
📏 {Config.OFFICE_RADIUS}m radius requirement
"""
        
        if is_admin:
            message += """

**🔐 Admin Commands:**
👨‍💼 `/add_admin <user_id>` - Add new admin
📅 `/exceptional_hours <user_id> <date> <start> <end> [reason]`
📊 `/admin_report` - Current day dashboard
👥 `/list_employees` - Employee directory
🖥️ `/server_status` - Server health status

**🕘 Admin Features:**
📈 Daily summary reports at 8 PM
🚨 Enhanced late arrival alerts
📊 Real-time attendance monitoring
⚙️ Exceptional working hours management
"""
        
        return message
    
    def format_error_message(self, error_type: str = "general", details: str = "") -> str:
        """
        Format error message for users.
        
        Args:
            error_type: Type of error
            details: Additional error details
            
        Returns:
            Formatted error message
        """
        messages = {
            "location_required": """
📍 **Location Required**

Please use the location sharing button to check in/out.
Manual entry is not allowed for security reasons.

🔒 This ensures accurate attendance tracking.
""",
            "not_registered": """
❌ **Registration Required**

Please register first using the /register command or the Register button.
""",
            "already_checked_in": """
⚠️ **Already Checked In**

You are already checked in today. Use the Check Out button to complete your workday.
""",
            "not_checked_in": """
⚠️ **Not Checked In**

You haven't checked in today. Please check in first before checking out.
""",
            "admin_required": """
❌ **Admin Privileges Required**

This command is only available for administrators.
""",
            "general": f"""
⚠️ **System Error**

An unexpected error occurred. Please try again.
{f"Details: {details}" if details else ""}

If the problem persists, contact an administrator.
"""
        }
        
        return messages.get(error_type, messages["general"])
    
    def format_conversation_prompt(self, prompt_type: str, context: Dict[str, Any]) -> str:
        """
        Format conversation prompts for multi-step interactions.
        
        Args:
            prompt_type: Type of prompt needed
            context: Context information
            
        Returns:
            Formatted prompt message
        """
        if prompt_type == "late_reason":
            work_start = context.get('work_start', Config.DEFAULT_WORK_START)
            current_time = context.get('current_time', datetime.now(self.timezone).strftime('%H:%M'))
            
            return f"""
⏰ **Late Check-in Detected**

Your work starts at {work_start}, but it's now {current_time}.

📝 Please provide a reason for being late:
(Type your reason in the next message)
"""
        
        elif prompt_type == "early_reason":
            work_end = context.get('work_end', Config.DEFAULT_WORK_END)
            current_time = context.get('current_time', datetime.now(self.timezone).strftime('%H:%M'))
            
            return f"""
⏰ **Early Check-out Detected**

Your work ends at {work_end}, but it's only {current_time}.

📝 Please provide a reason for leaving early:
(Type your reason in the next message)
"""
        
        return "Please provide additional information:" 