from datetime import datetime
import pytz
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

import sys
import os
# Add parent directory to sys.path to import config.py directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database_enhanced import EnhancedAttendanceDatabase
from location_utils import is_within_radius

# Import config from renamed file to avoid directory conflict
from bot_config import Config

class EnhancedEmployeeHandlers:
    """Enhanced handler class for employee-related commands and interactions"""
    
    def __init__(self, db: EnhancedAttendanceDatabase):
        self.db = db
        self.config = Config
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        if not self.db.is_employee_registered(user.id):
            await update.message.reply_text(
                f"👋 Welcome to Enhanced Attendance System!\n\n"
                f"Hello {user.first_name}! You need to register first to use this bot.\n"
                f"Please click the 'Register' button below to share your contact information.",
                reply_markup=self.get_registration_keyboard()
            )
        else:
            # Check current status
            status = self.db.get_attendance_status(user.id)
            is_checked_in = status and status[2] == 'checked_in'
            
            await update.message.reply_text(
                f"👋 Welcome back, {user.first_name}!\n\n"
                f"🏢 Office Location: El Mansoura (29R3+7Q)\n"
                f"📏 Attendance Radius: {self.config.OFFICE_RADIUS}m\n\n"
                f"Use the buttons below to check in/out or view your status.",
                reply_markup=self.get_location_only_keyboard(is_checked_in)
            )
    
    def get_location_only_keyboard(self, is_checked_in=False):
        """Get keyboard that ONLY allows location sharing for attendance"""
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
        
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_registration_keyboard(self):
        """Get registration keyboard for new users"""
        keyboard = [[KeyboardButton("📝 Register", request_contact=True)]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    def get_contact_sharing_keyboard(self):
        """Get contact sharing keyboard"""
        keyboard = [[KeyboardButton("📝 Share Contact", request_contact=True)]]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /register command"""
        user = update.effective_user
        
        if self.db.is_employee_registered(user.id):
            await update.message.reply_text("✅ You are already registered!")
            return
        
        await update.message.reply_text(
            "📝 Please share your contact information by clicking the 'Share Contact' button below.",
            reply_markup=self.get_contact_sharing_keyboard(),
            parse_mode='Markdown'
        )
    
    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle contact sharing for registration"""
        user = update.effective_user
        contact = update.message.contact
        
        # Register the employee
        self.db.register_employee(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=contact.phone_number
        )
        
        await update.message.reply_text(
            "✅ Contact information shared successfully!",
            reply_markup=self.get_location_only_keyboard(False),
            parse_mode='Markdown'
        )
    
    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle location sharing for check-in/check-out with STRICT location requirement"""
        user = update.effective_user
        location = update.message.location
        
        if not self.db.is_employee_registered(user.id):
            await update.message.reply_text("❌ Please register first using /register")
            return
        
        # STRICT LOCATION VERIFICATION - No bypass allowed
        within_radius, distance = is_within_radius(
            location.latitude, location.longitude,
            self.config.OFFICE_LATITUDE, self.config.OFFICE_LONGITUDE, 
            self.config.OFFICE_RADIUS
        )
        
        if not within_radius:
            await update.message.reply_text(
                f"❌ **Location Verification Failed**\n\n"
                f"You are {distance:.0f}m away from the office.\n"
                f"Attendance is ONLY allowed within {self.config.OFFICE_RADIUS}m of the office.\n\n"
                f"🏢 Office Location: 29R3+7Q El Mansoura 1\n"
                f"📱 Please move closer and try again.\n\n"
                f"⚠️ Manual location entry is disabled for security.",
                parse_mode='Markdown'
            )
            return
        
        # Check current status to determine check-in or check-out
        status = self.db.get_attendance_status(user.id)
        
        if not status or status[2] == 'checked_out':
            await self._handle_enhanced_checkin(update, location, distance)
        elif status[2] == 'checked_in':
            await self._handle_enhanced_checkout(update, location, distance, status)
    
    async def _handle_enhanced_checkin(self, update: Update, location, distance):
        """Handle enhanced check-in with late reason prompt"""
        user = update.effective_user
        
        # Check if this would be a late check-in
        is_late = self.db.is_late_checkin(user.id)
        
        if is_late:
            # Set conversation state to expect late reason
            self.db.set_conversation_state(
                user.id, 
                'waiting_late_reason', 
                f"{location.latitude},{location.longitude},{distance}"
            )
            
            # Get work hours for context
            work_start, _ = self.db.get_effective_work_hours(user.id)
            current_time = datetime.now(pytz.timezone('Africa/Cairo')).time()
            
            await update.message.reply_text(
                f"⏰ **Late Check-in Detected**\n\n"
                f"Your work starts at {work_start}, but it's now {current_time.strftime('%H:%M')}.\n\n"
                f"📝 Please provide a reason for being late:\n"
                f"(Type your reason in the next message)",
                parse_mode='Markdown'
            )
            return
        
        # Normal check-in (not late)
        success, message, _ = self.db.check_in_with_reason(
            user.id, location.latitude, location.longitude
        )
        
        if success:
            time_str = message.split('at ')[1]
            await update.message.reply_text(
                f"✅ **Check-In Successful!**\n\n"
                f"⏰ Time: {time_str}\n"
                f"📍 Distance from office: {distance:.0f}m\n"
                f"🌐 Location: {location.latitude:.6f}, {location.longitude:.6f}\n"
                f"✨ On time - Great job!",
                reply_markup=self.get_location_only_keyboard(True),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ {message}")
    
    async def _handle_enhanced_checkout(self, update: Update, location, distance, status):
        """Handle enhanced check-out with early reason prompt"""
        user = update.effective_user
        
        # Check if this would be an early check-out
        is_early = self.db.is_early_checkout(user.id)
        
        if is_early:
            # Set conversation state to expect early checkout reason
            self.db.set_conversation_state(
                user.id,
                'waiting_early_reason',
                f"{location.latitude},{location.longitude},{distance}"
            )
            
            # Get work hours for context
            _, work_end = self.db.get_effective_work_hours(user.id)
            current_time = datetime.now(pytz.timezone('Africa/Cairo')).time()
            
            await update.message.reply_text(
                f"⏰ **Early Check-out Detected**\n\n"
                f"Your work ends at {work_end}, but it's only {current_time.strftime('%H:%M')}.\n\n"
                f"📝 Please provide a reason for leaving early:\n"
                f"(Type your reason in the next message)",
                parse_mode='Markdown'
            )
            return
        
        # Normal check-out (not early)
        success, message, _ = self.db.check_out_with_reason(
            user.id, location.latitude, location.longitude
        )
        
        if success:
            check_in_time = datetime.fromisoformat(status[0])
            check_out_time = datetime.now(pytz.timezone(self.config.TIMEZONE))
            work_duration = check_out_time - check_in_time
            time_str = message.split('at ')[1]
            hours, remainder = divmod(work_duration.total_seconds(), 3600)
            minutes = remainder // 60
            
            await update.message.reply_text(
                f"✅ **Check-Out Successful!**\n\n"
                f"⏰ Time: {time_str}\n"
                f"⏱️ Work Duration: {int(hours)}h {int(minutes)}m\n"
                f"📍 Distance from office: {distance:.0f}m\n"
                f"🌐 Location: {location.latitude:.6f}, {location.longitude:.6f}\n"
                f"✨ Full workday completed!",
                reply_markup=self.get_location_only_keyboard(False),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ {message}")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages based on conversation state"""
        user = update.effective_user
        text = update.message.text
        
        # Check conversation state
        state, data = self.db.get_conversation_state(user.id)
        
        if state == 'waiting_late_reason':
            await self._process_late_reason(update, text, data)
        elif state == 'waiting_early_reason':
            await self._process_early_reason(update, text, data)
        elif text in ["🟢 Check In", "🔴 Check Out"]:
            # If user tries to use text buttons instead of location
            await update.message.reply_text(
                "📍 **Location Required**\n\n"
                "Please use the location sharing button to check in/out.\n"
                "Manual entry is not allowed for security reasons.\n\n"
                "🔒 This ensures accurate attendance tracking.",
                parse_mode='Markdown'
            )
        else:
            await self._handle_other_commands(update, text)
    
    async def _process_late_reason(self, update: Update, reason: str, location_data: str):
        """Process late check-in reason"""
        user = update.effective_user
        lat_str, lon_str, distance_str = location_data.split(',')
        
        latitude = float(lat_str)
        longitude = float(lon_str)
        distance = float(distance_str)
        
        # Perform check-in with reason
        success, message, is_late = self.db.check_in_with_reason(
            user.id, latitude, longitude, reason
        )
        
        # Clear conversation state
        self.db.clear_conversation_state(user.id)
        
        if success:
            time_str = message.split('at ')[1]
            await update.message.reply_text(
                f"✅ **Late Check-In Recorded**\n\n"
                f"⏰ Time: {time_str}\n"
                f"📍 Distance from office: {distance:.0f}m\n"
                f"📝 Reason: {reason}\n\n"
                f"✨ Thank you for providing the reason!",
                reply_markup=self.get_location_only_keyboard(True),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ {message}")
    
    async def _process_early_reason(self, update: Update, reason: str, location_data: str):
        """Process early check-out reason"""
        user = update.effective_user
        lat_str, lon_str, distance_str = location_data.split(',')
        
        latitude = float(lat_str)
        longitude = float(lon_str)
        distance = float(distance_str)
        
        # Perform check-out with reason
        success, message, is_early = self.db.check_out_with_reason(
            user.id, latitude, longitude, reason
        )
        
        # Clear conversation state
        self.db.clear_conversation_state(user.id)
        
        if success:
            time_str = message.split('at ')[1]
            # Calculate work duration
            status = self.db.get_attendance_status(user.id)
            if status:
                check_in_time = datetime.fromisoformat(status[0])
                check_out_time = datetime.now(pytz.timezone(self.config.TIMEZONE))
                work_duration = check_out_time - check_in_time
                hours, remainder = divmod(work_duration.total_seconds(), 3600)
                minutes = remainder // 60
                
                await update.message.reply_text(
                    f"✅ **Early Check-Out Recorded**\n\n"
                    f"⏰ Time: {time_str}\n"
                    f"⏱️ Work Duration: {int(hours)}h {int(minutes)}m\n"
                    f"📍 Distance from office: {distance:.0f}m\n"
                    f"📝 Reason: {reason}\n\n"
                    f"✨ Thank you for providing the reason!",
                    reply_markup=self.get_location_only_keyboard(False),
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(f"❌ {message}")
    
    async def _handle_other_commands(self, update: Update, text: str):
        """Handle other commands like status, reports, etc."""
        user = update.effective_user
        
        if text == "📊 My Status":
            await self._show_status(update)
        elif text == "📈 My Report":
            await self._show_report(update)
        elif text == "ℹ️ Help":
            await self._show_help(update)
        else:
            await update.message.reply_text(
                "❓ **Unknown Command**\n\n"
                "Please use the buttons provided or type /help for assistance.",
                parse_mode='Markdown'
            )
    
    async def _show_status(self, update: Update):
        """Show current attendance status"""
        user = update.effective_user
        status = self.db.get_attendance_status(user.id)
        egypt_tz = pytz.timezone(self.config.TIMEZONE)
        today = datetime.now(egypt_tz).date().strftime('%Y-%m-%d')
        
        if not status:
            work_start, work_end = self.db.get_effective_work_hours(user.id)
            await update.message.reply_text(
                f"📊 **Attendance Status - {today}**\n\n"
                f"❌ Not checked in today\n"
                f"⏰ Work Hours: {work_start} - {work_end}\n"
                f"💡 Use the 'Check In' button to record your attendance",
                parse_mode='Markdown'
            )
        else:
            check_in_time = datetime.fromisoformat(status[0])
            if status[1]:  # Checked out
                check_out_time = datetime.fromisoformat(status[1])
                duration = check_out_time - check_in_time
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes = remainder // 60
                
                await update.message.reply_text(
                    f"📊 **Attendance Status - {today}**\n\n"
                    f"✅ Checked in: {check_in_time.strftime('%H:%M:%S')}\n"
                    f"✅ Checked out: {check_out_time.strftime('%H:%M:%S')}\n"
                    f"⏱️ Work duration: {int(hours)}h {int(minutes)}m",
                    parse_mode='Markdown'
                )
            else:  # Still checked in
                current_time = datetime.now(egypt_tz)
                duration = current_time - check_in_time
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes = remainder // 60
                
                await update.message.reply_text(
                    f"📊 **Attendance Status - {today}**\n\n"
                    f"✅ Checked in: {check_in_time.strftime('%H:%M:%S')}\n"
                    f"⏳ Currently working\n"
                    f"⏱️ Duration so far: {int(hours)}h {int(minutes)}m",
                    parse_mode='Markdown'
                )
    
    async def _show_report(self, update: Update):
        """Show attendance report for last 7 days"""
        user = update.effective_user
        
        with self.db.db_name as db_path:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT date, check_in_time, check_out_time, is_late, is_early_checkout, 
                       late_reason, early_checkout_reason
                FROM attendance 
                WHERE telegram_id = ?
                ORDER BY date DESC
                LIMIT 7
            ''', (user.id,))
            
            records = cursor.fetchall()
            conn.close()
        
        if not records:
            await update.message.reply_text(
                "📈 **Attendance Report**\n\n"
                "No attendance records found.",
                parse_mode='Markdown'
            )
            return
        
        report = "📈 **Attendance Report (Last 7 Days)**\n\n"
        
        for record in records:
            date_str = record[0]
            check_in = record[1]
            check_out = record[2]
            is_late = record[3]
            is_early = record[4]
            late_reason = record[5]
            early_reason = record[6]
            
            report += f"📅 **{date_str}**\n"
            
            if check_in:
                check_in_time = datetime.fromisoformat(check_in).strftime('%H:%M:%S')
                report += f"🟢 In: {check_in_time}"
                if is_late:
                    report += f" (⏰ Late)"
                    if late_reason:
                        report += f" - {late_reason}"
                report += "\n"
            
            if check_out:
                check_out_time = datetime.fromisoformat(check_out).strftime('%H:%M:%S')
                report += f"🔴 Out: {check_out_time}"
                if is_early:
                    report += f" (⏰ Early)"
                    if early_reason:
                        report += f" - {early_reason}"
                report += "\n"
            elif check_in:
                report += "🔴 Out: Not recorded\n"
            
            report += "\n"
        
        await update.message.reply_text(report, parse_mode='Markdown')
    
    async def _show_help(self, update: Update):
        """Show help information"""
        help_text = """
ℹ️ **Attendance System Help**

**How to Check In/Out:**
📍 Use the location-sharing buttons only
🚫 Manual location entry is disabled
✅ Must be within 100m of office

**Work Hours:**
⏰ Standard: 09:00 - 17:00
📝 Late check-ins require a reason
📝 Early check-outs require a reason

**Commands:**
📊 My Status - View today's attendance
📈 My Report - View recent attendance history
🔄 Use buttons for check-in/out

**Security:**
🔒 Location verification is mandatory
📱 GPS must be enabled
🏢 Office location: 29R3+7Q El Mansoura 1
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown') 