from datetime import datetime
import pytz
from telegram import Update
from telegram.ext import ContextTypes

from database import AttendanceDatabase
from location_utils import is_within_radius
from utils.keyboards import Keyboards
from utils.messages import Messages
from config.settings import OFFICE_LATITUDE, OFFICE_LONGITUDE, OFFICE_RADIUS, TIMEZONE

class EmployeeHandlers:
    """Handler class for employee-related commands and interactions"""
    
    def __init__(self, db: AttendanceDatabase):
        self.db = db
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        if not self.db.is_employee_registered(user.id):
            await update.message.reply_text(
                Messages.welcome_new_user(user.first_name),
                reply_markup=Keyboards.get_registration_keyboard()
            )
        else:
            # Check current status
            status = self.db.get_attendance_status(user.id)
            is_checked_in = status and status[2] == 'checked_in'
            
            await update.message.reply_text(
                Messages.welcome_back(user.first_name),
                reply_markup=Keyboards.get_main_keyboard(is_checked_in)
            )
    
    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /register command"""
        user = update.effective_user
        
        if self.db.is_employee_registered(user.id):
            await update.message.reply_text("✅ You are already registered!")
            return
        
        await update.message.reply_text(
            Messages.registration_request(),
            reply_markup=Keyboards.get_contact_sharing_keyboard(),
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
            Messages.registration_success(user, contact.phone_number),
            reply_markup=Keyboards.get_main_keyboard(False),
            parse_mode='Markdown'
        )
    
    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle location sharing for check-in/check-out"""
        user = update.effective_user
        location = update.message.location
        
        if not self.db.is_employee_registered(user.id):
            await update.message.reply_text("❌ Please register first using /register")
            return
        
        # Check if location is within office radius
        within_radius, distance = is_within_radius(
            location.latitude, location.longitude,
            OFFICE_LATITUDE, OFFICE_LONGITUDE, OFFICE_RADIUS
        )
        
        if not within_radius:
            await update.message.reply_text(
                Messages.location_error(distance),
                parse_mode='Markdown'
            )
            return
        
        # Check current status to determine check-in or check-out
        status = self.db.get_attendance_status(user.id)
        
        if not status or status[2] == 'checked_out':
            await self._handle_checkin(update, location, distance)
        elif status[2] == 'checked_in':
            await self._handle_checkout(update, location, distance, status)
    
    async def _handle_checkin(self, update: Update, location, distance):
        """Handle check-in process"""
        user = update.effective_user
        success, message = self.db.check_in(user.id, location.latitude, location.longitude)
        
        if success:
            time_str = message.split('at ')[1]
            await update.message.reply_text(
                Messages.checkin_success(time_str, distance, location.latitude, location.longitude),
                reply_markup=Keyboards.get_main_keyboard(True),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ {message}")
    
    async def _handle_checkout(self, update: Update, location, distance, status):
        """Handle check-out process"""
        user = update.effective_user
        success, message = self.db.check_out(user.id, location.latitude, location.longitude)
        
        if success:
            check_in_time = datetime.fromisoformat(status[0])
            check_out_time = datetime.now(pytz.timezone(TIMEZONE))
            work_duration = check_out_time - check_in_time
            time_str = message.split('at ')[1]
            
            await update.message.reply_text(
                Messages.checkout_success(time_str, work_duration, distance, 
                                        location.latitude, location.longitude),
                reply_markup=Keyboards.get_main_keyboard(False),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ {message}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user = update.effective_user
        
        if not self.db.is_employee_registered(user.id):
            await update.message.reply_text("❌ Please register first using /register")
            return
        
        status = self.db.get_attendance_status(user.id)
        
        if not status:
            await update.message.reply_text(Messages.attendance_status_not_checked_in())
        else:
            await update.message.reply_text(
                Messages.attendance_status(status), 
                parse_mode='Markdown'
            )
    
    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /report command"""
        user = update.effective_user
        
        if not self.db.is_employee_registered(user.id):
            await update.message.reply_text("❌ Please register first using /register")
            return
        
        # Get last 7 days report
        report_data = self.db.get_employee_attendance_report(user.id, 7)
        
        if not report_data:
            await update.message.reply_text("📈 No attendance records found for the last 7 days.")
            return
        
        report_text = f"📈 **Attendance Report - Last 7 Days**\n\n"
        
        for record in report_data:
            date = record[0]
            check_in = datetime.fromisoformat(record[1]).strftime('%H:%M') if record[1] else "N/A"
            check_out = datetime.fromisoformat(record[2]).strftime('%H:%M') if record[2] else "N/A"
            status = record[3]
            
            # Calculate work duration if both times exist
            duration = ""
            if record[1] and record[2]:
                check_in_dt = datetime.fromisoformat(record[1])
                check_out_dt = datetime.fromisoformat(record[2])
                work_duration = check_out_dt - check_in_dt
                hours, remainder = divmod(work_duration.total_seconds(), 3600)
                minutes = remainder // 60
                duration = f" ({int(hours)}h {int(minutes)}m)"
            
            report_text += f"📅 **{date}**\n"
            report_text += f"   🟢 In: {check_in} | 🔴 Out: {check_out}{duration}\n"
            report_text += f"   📊 Status: {status.replace('_', ' ').title()}\n\n"
        
        await update.message.reply_text(report_text, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user = update.effective_user
        is_admin = self.db.is_admin(user.id) if self.db.is_employee_registered(user.id) else False
        
        await update.message.reply_text(
            Messages.help_text(is_admin), 
            parse_mode='Markdown'
        )

    async def reminders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle reminder settings for employees"""
        user = update.effective_user
        
        if not self.db.is_employee_registered(user.id):
            await update.message.reply_text("❌ Please register first using /register")
            return
        
        await update.message.reply_text(
            Messages.reminder_settings(),
            reply_markup=Keyboards.get_reminder_settings_keyboard(),
            parse_mode='Markdown'
        )

    async def set_reminder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set reminder time via command"""
        user = update.effective_user
        
        if not self.db.is_employee_registered(user.id):
            await update.message.reply_text("❌ Please register first using /register")
            return
        
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ Usage: `/set_reminder checkin HH:MM` or `/set_reminder checkout HH:MM`\n"
                "Example: `/set_reminder checkin 09:00`",
                parse_mode='Markdown'
            )
            return
        
        reminder_type = context.args[0].lower()
        time_str = context.args[1]
        
        # Validate time format
        try:
            datetime.strptime(time_str, '%H:%M')
        except ValueError:
            await update.message.reply_text("❌ Invalid time format. Use HH:MM (24-hour format)")
            return
        
        if reminder_type == "checkin":
            self.db.update_reminder_settings(user.id, reminder_time=time_str, reminder_enabled=True)
            await update.message.reply_text(f"✅ Check-in reminder set to {time_str}")
        elif reminder_type == "checkout":
            self.db.update_reminder_settings(user.id, checkout_reminder_time=time_str, checkout_reminder_enabled=True)
            await update.message.reply_text(f"✅ Check-out reminder set to {time_str}")
        else:
            await update.message.reply_text("❌ Invalid reminder type. Use 'checkin' or 'checkout'") 