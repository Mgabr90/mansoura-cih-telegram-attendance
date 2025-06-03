import os
import logging
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import io
import asyncio
import sqlite3

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

from database import AttendanceDatabase
from location_utils import is_within_radius, calculate_distance, format_location_message
from notification_service import NotificationService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
OFFICE_LAT = float(os.getenv('OFFICE_LATITUDE', 31.0417))
OFFICE_LON = float(os.getenv('OFFICE_LONGITUDE', 31.3778))
OFFICE_RADIUS = int(os.getenv('OFFICE_RADIUS', 100))

# Initialize database
db = AttendanceDatabase()

class AttendanceBot:
    def __init__(self):
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.notification_service = NotificationService(BOT_TOKEN, db)
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all command and message handlers"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("register", self.register_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("report", self.report_command))
        self.app.add_handler(CommandHandler("admin", self.admin_command))
        self.app.add_handler(CommandHandler("add_admin", self.add_admin_command))
        self.app.add_handler(CommandHandler("all_report", self.all_report_command))
        
        # Export commands (admin only)
        self.app.add_handler(CommandHandler("export_daily", self.export_daily_command))
        self.app.add_handler(CommandHandler("export_monthly", self.export_monthly_command))
        self.app.add_handler(CommandHandler("export_employees", self.export_employees_command))
        self.app.add_handler(CommandHandler("export_attendance", self.export_attendance_command))
        
        # Reminder and notification commands
        self.app.add_handler(CommandHandler("reminders", self.reminders_command))
        self.app.add_handler(CommandHandler("set_reminder", self.set_reminder_command))
        self.app.add_handler(CommandHandler("admin_alerts", self.admin_alerts_command))
        
        # Location handler for check-in/check-out
        self.app.add_handler(MessageHandler(filters.LOCATION, self.handle_location))
        
        # Callback query handler for inline buttons
        self.app.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Contact handler for registration
        self.app.add_handler(MessageHandler(filters.CONTACT, self.handle_contact))
    
    def get_main_keyboard(self, is_checked_in=False):
        """Get the main keyboard based on check-in status"""
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
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        
        if not db.is_employee_registered(user.id):
            keyboard = [[KeyboardButton("📝 Register", request_contact=True)]]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
            
            await update.message.reply_text(
                f"👋 Welcome to El Mansoura Attendance System!\n\n"
                f"Hello {user.first_name}! You need to register first to use this bot.\n"
                f"Please click the 'Register' button below to share your contact information.",
                reply_markup=reply_markup
            )
        else:
            # Check current status
            status = db.get_attendance_status(user.id)
            is_checked_in = status and status[2] == 'checked_in'
            
            await update.message.reply_text(
                f"👋 Welcome back, {user.first_name}!\n\n"
                f"🏢 Office Location: El Mansoura (29R3+7Q)\n"
                f"📏 Attendance Radius: {OFFICE_RADIUS}m\n\n"
                f"Use the buttons below to check in/out or view your status.",
                reply_markup=self.get_main_keyboard(is_checked_in)
            )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user = update.effective_user
        is_admin = db.is_admin(user.id) if db.is_employee_registered(user.id) else False
        
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
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /register command"""
        user = update.effective_user
        
        if db.is_employee_registered(user.id):
            await update.message.reply_text("✅ You are already registered!")
            return
        
        keyboard = [[KeyboardButton("📝 Share Contact", request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            "📝 **Employee Registration**\n\n"
            "Please share your contact information to complete registration.",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle contact sharing for registration"""
        user = update.effective_user
        contact = update.message.contact
        
        # Register the employee
        db.register_employee(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=contact.phone_number
        )
        
        await update.message.reply_text(
            f"✅ **Registration Successful!**\n\n"
            f"👤 Name: {user.first_name} {user.last_name or ''}\n"
            f"📱 Phone: {contact.phone_number}\n"
            f"🆔 Username: @{user.username or 'N/A'}\n\n"
            f"You can now use the attendance system!",
            reply_markup=self.get_main_keyboard(False),
            parse_mode='Markdown'
        )
    
    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle location sharing for check-in/check-out"""
        user = update.effective_user
        location = update.message.location
        
        if not db.is_employee_registered(user.id):
            await update.message.reply_text("❌ Please register first using /register")
            return
        
        # Check if location is within office radius
        within_radius, distance = is_within_radius(
            location.latitude, location.longitude,
            OFFICE_LAT, OFFICE_LON, OFFICE_RADIUS
        )
        
        if not within_radius:
            await update.message.reply_text(
                f"❌ **Location Error**\n\n"
                f"You are {distance:.0f}m away from the office.\n"
                f"Please move closer to the office (within {OFFICE_RADIUS}m radius).\n\n"
                f"🏢 Office Location: 29R3+7Q El Mansoura 1",
                parse_mode='Markdown'
            )
            return
        
        # Check current status to determine check-in or check-out
        status = db.get_attendance_status(user.id)
        
        if not status or status[2] == 'checked_out':
            # Check in
            success, message = db.check_in(user.id, location.latitude, location.longitude)
            if success:
                await update.message.reply_text(
                    f"✅ **Check-In Successful!**\n\n"
                    f"⏰ Time: {message.split('at ')[1]}\n"
                    f"📍 Distance from office: {distance:.0f}m\n"
                    f"🌐 Location: {location.latitude:.6f}, {location.longitude:.6f}",
                    reply_markup=self.get_main_keyboard(True),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"❌ {message}")
        
        elif status[2] == 'checked_in':
            # Check out
            success, message = db.check_out(user.id, location.latitude, location.longitude)
            if success:
                check_in_time = datetime.fromisoformat(status[0])
                check_out_time = datetime.now(pytz.timezone('Africa/Cairo'))
                work_duration = check_out_time - check_in_time
                hours, remainder = divmod(work_duration.total_seconds(), 3600)
                minutes = remainder // 60
                
                await update.message.reply_text(
                    f"✅ **Check-Out Successful!**\n\n"
                    f"⏰ Time: {message.split('at ')[1]}\n"
                    f"⏱️ Work Duration: {int(hours)}h {int(minutes)}m\n"
                    f"📍 Distance from office: {distance:.0f}m\n"
                    f"🌐 Location: {location.latitude:.6f}, {location.longitude:.6f}",
                    reply_markup=self.get_main_keyboard(False),
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(f"❌ {message}")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        user = update.effective_user
        
        if not db.is_employee_registered(user.id):
            await update.message.reply_text("❌ Please register first using /register")
            return
        
        status = db.get_attendance_status(user.id)
        egypt_tz = pytz.timezone('Africa/Cairo')
        today = datetime.now(egypt_tz).date().strftime('%Y-%m-%d')
        
        if not status:
            await update.message.reply_text(
                f"📊 **Attendance Status - {today}**\n\n"
                f"❌ Not checked in today\n"
                f"💡 Use the 'Check In' button to record your attendance"
            )
        else:
            check_in_time = datetime.fromisoformat(status[0]) if status[0] else None
            check_out_time = datetime.fromisoformat(status[1]) if status[1] else None
            
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
            
            status_text += f"\n📈 Status: {status[2].replace('_', ' ').title()}"
            
            await update.message.reply_text(status_text, parse_mode='Markdown')
    
    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /report command"""
        user = update.effective_user
        
        if not db.is_employee_registered(user.id):
            await update.message.reply_text("❌ Please register first using /register")
            return
        
        # Get last 7 days report
        report_data = db.get_employee_attendance_report(user.id, 7)
        
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
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user = update.effective_user
        
        if not db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 Today's Report", callback_data="admin_today_report")],
            [InlineKeyboardButton("📈 All Employees Report", callback_data="admin_all_report")],
            [InlineKeyboardButton("📁 Export Data", callback_data="admin_export_menu")],
            [InlineKeyboardButton("👥 Employee List", callback_data="admin_employee_list")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔧 **Admin Panel**\n\nSelect an option:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def add_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add_admin command"""
        user = update.effective_user
        
        if not db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Please provide a user ID: /add_admin <user_id>")
            return
        
        try:
            new_admin_id = int(context.args[0])
            db.add_admin(new_admin_id)
            await update.message.reply_text(f"✅ User {new_admin_id} has been added as admin.")
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")
    
    async def all_report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /all_report command"""
        user = update.effective_user
        
        if not db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        report_data = db.get_all_employees_report()
        egypt_tz = pytz.timezone('Africa/Cairo')
        today = datetime.now(egypt_tz).date().strftime('%Y-%m-%d')
        
        if not report_data:
            await update.message.reply_text("📊 No employee data found.")
            return
        
        report_text = f"📊 **All Employees Report - {today}**\n\n"
        
        for record in report_data:
            name = f"{record[0] or ''} {record[1] or ''}".strip() or "Unknown"
            username = f"@{record[2]}" if record[2] else "No username"
            check_in = datetime.fromisoformat(record[3]).strftime('%H:%M') if record[3] else "❌"
            check_out = datetime.fromisoformat(record[4]).strftime('%H:%M') if record[4] else "❌"
            status = record[5] or "Absent"
            
            report_text += f"👤 **{name}** ({username})\n"
            report_text += f"   🟢 In: {check_in} | 🔴 Out: {check_out}\n"
            report_text += f"   📊 Status: {status.replace('_', ' ').title()}\n\n"
        
        # Split long messages if needed
        if len(report_text) > 4000:
            parts = [report_text[i:i+4000] for i in range(0, len(report_text), 4000)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='Markdown')
        else:
            await update.message.reply_text(report_text, parse_mode='Markdown')
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        
        if query.data == "admin_today_report":
            await self.all_report_command(update, context)
            
        elif query.data == "admin_export_menu":
            keyboard = [
                [InlineKeyboardButton("📊 Daily CSV", callback_data="export_daily_today")],
                [InlineKeyboardButton("📈 Monthly CSV", callback_data="export_monthly_current")],
                [InlineKeyboardButton("👥 Employee List CSV", callback_data="export_employees_list")],
                [InlineKeyboardButton("📁 Full Attendance CSV", callback_data="export_attendance_30days")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📁 **Export Data Menu**\n\nChoose export type:",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        elif query.data in ["export_daily_today", "export_monthly_current", "export_employees_list", "export_attendance_30days"]:
            if query.data == "export_daily_today":
                await self.export_daily_command(update, context)
            elif query.data == "export_monthly_current":
                await self.export_monthly_command(update, context)
            elif query.data == "export_employees_list":
                await self.export_employees_command(update, context)
            elif query.data == "export_attendance_30days":
                await self.export_attendance_command(update, context)
                
        # Reminder callbacks
        elif query.data == "set_checkin_reminder":
            await query.edit_message_text(
                "⏰ **Set Check-in Reminder**\n\n"
                "Use: `/set_reminder checkin HH:MM`\n"
                "Example: `/set_reminder checkin 09:00`\n\n"
                "This will remind you to check in at the specified time.",
                parse_mode='Markdown'
            )
            
        elif query.data == "set_checkout_reminder":
            await query.edit_message_text(
                "🔔 **Set Check-out Reminder**\n\n"
                "Use: `/set_reminder checkout HH:MM`\n"
                "Example: `/set_reminder checkout 17:00`\n\n"
                "This will remind you to check out at the specified time.",
                parse_mode='Markdown'
            )
            
        elif query.data == "disable_reminders":
            db.update_reminder_settings(user.id, reminder_enabled=False, checkout_reminder_enabled=False)
            await query.edit_message_text(
                "🔇 **Reminders Disabled**\n\n"
                "You will no longer receive attendance reminders.\n"
                "You can re-enable them anytime using /reminders command.",
                parse_mode='Markdown'
            )
            
        elif query.data == "view_reminder_settings":
            # Get current settings from database
            with sqlite3.connect(db.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT reminder_enabled, reminder_time, checkout_reminder_enabled, checkout_reminder_time
                    FROM employees WHERE telegram_id = ?
                ''', (user.id,))
                settings = cursor.fetchone()
            
            if settings:
                reminder_enabled, reminder_time, checkout_reminder_enabled, checkout_reminder_time = settings
                status_text = f"""
📊 **Your Reminder Settings**

⏰ **Check-in Reminder:**
Status: {'Enabled' if reminder_enabled else 'Disabled'}
Time: {reminder_time if reminder_enabled else 'Not set'}

🔔 **Check-out Reminder:**
Status: {'Enabled' if checkout_reminder_enabled else 'Disabled'}
Time: {checkout_reminder_time if checkout_reminder_enabled else 'Not set'}
                """
            else:
                status_text = "❌ No settings found. Please register first."
            
            await query.edit_message_text(status_text, parse_mode='Markdown')
            
        # Admin alert callbacks
        elif query.data == "toggle_admin_alerts":
            if db.is_admin(user.id):
                current_setting, threshold = db.get_admin_alert_settings(user.id)
                new_setting = not current_setting
                db.update_admin_alert_settings(user.id, alert_enabled=new_setting)
                
                status = "enabled" if new_setting else "disabled"
                await query.edit_message_text(
                    f"🔄 **Alert Settings Updated**\n\n"
                    f"Admin alerts are now {status}.",
                    parse_mode='Markdown'
                )
                
        elif query.data == "set_late_threshold":
            await query.edit_message_text(
                "⏱️ **Set Late Threshold**\n\n"
                "Contact your system administrator to set a custom late threshold.\n"
                "Default: 30 minutes",
                parse_mode='Markdown'
            )
            
        elif query.data == "test_admin_alert":
            if db.is_admin(user.id):
                test_message = """
🧪 **Test Alert**

This is a test admin alert to verify your notification settings are working correctly.

✅ If you received this message, alerts are configured properly.
                """
                await query.message.reply_text(test_message, parse_mode='Markdown')
    
    async def export_daily_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Export daily attendance report as CSV"""
        user = update.effective_user
        
        if not db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        # Parse date if provided, otherwise use today
        egypt_tz = pytz.timezone('Africa/Cairo')
        date = datetime.now(egypt_tz).date()
        
        if context.args:
            try:
                date = datetime.strptime(context.args[0], '%Y-%m-%d').date()
            except ValueError:
                await update.message.reply_text("❌ Invalid date format. Use YYYY-MM-DD")
                return
        
        # Get data
        data = db.get_daily_summary_csv(date)
        headers = ['Full Name', 'Username', 'Check In', 'Check Out', 'Work Hours', 'Status']
        
        # Create CSV
        csv_content = db.create_csv_string(data, headers)
        
        # Send as file
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = f"daily_attendance_{date}.csv"
        
        await update.message.reply_document(
            document=csv_file,
            caption=f"📊 Daily Attendance Report - {date}\n📁 {len(data)} employees"
        )

    async def export_monthly_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Export monthly attendance report as CSV"""
        user = update.effective_user
        
        if not db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        # Parse year and month if provided
        egypt_tz = pytz.timezone('Africa/Cairo')
        now = datetime.now(egypt_tz)
        year, month = now.year, now.month
        
        if context.args:
            try:
                if len(context.args) >= 1:
                    year = int(context.args[0])
                if len(context.args) >= 2:
                    month = int(context.args[1])
            except ValueError:
                await update.message.reply_text("❌ Invalid format. Use: /export_monthly [YYYY] [MM]")
                return
        
        # Get data
        data = db.get_monthly_report_csv(year, month)
        headers = ['Full Name', 'Username', 'Days Present', 'Avg Work Hours', 'Total Work Hours']
        
        # Create CSV
        csv_content = db.create_csv_string(data, headers)
        
        # Send as file
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = f"monthly_attendance_{year}_{month:02d}.csv"
        
        await update.message.reply_document(
            document=csv_file,
            caption=f"📊 Monthly Attendance Report - {year}/{month:02d}\n📁 {len(data)} employees"
        )

    async def export_employees_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Export employee list as CSV"""
        user = update.effective_user
        
        if not db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        # Get data
        data = db.get_employee_list_csv()
        headers = ['Telegram ID', 'Full Name', 'Username', 'Phone Number', 'Registration Date', 'Status']
        
        # Create CSV
        csv_content = db.create_csv_string(data, headers)
        
        # Send as file
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = f"employee_list_{datetime.now().strftime('%Y%m%d')}.csv"
        
        await update.message.reply_document(
            document=csv_file,
            caption=f"👥 Employee List Export\n📁 {len(data)} employees"
        )

    async def export_attendance_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Export detailed attendance data as CSV"""
        user = update.effective_user
        
        if not db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        # Parse date range if provided
        egypt_tz = pytz.timezone('Africa/Cairo')
        end_date = datetime.now(egypt_tz).date()
        start_date = end_date - timedelta(days=30)  # Default last 30 days
        
        if context.args:
            try:
                if len(context.args) >= 1:
                    start_date = datetime.strptime(context.args[0], '%Y-%m-%d').date()
                if len(context.args) >= 2:
                    end_date = datetime.strptime(context.args[1], '%Y-%m-%d').date()
            except ValueError:
                await update.message.reply_text("❌ Invalid date format. Use: /export_attendance [YYYY-MM-DD] [YYYY-MM-DD]")
                return
        
        # Get data
        data = db.export_attendance_csv(start_date, end_date)
        headers = [
            'Full Name', 'Username', 'Phone Number', 'Date', 
            'Check In Time', 'Check Out Time', 'Work Hours', 'Status',
            'Check In Latitude', 'Check In Longitude', 
            'Check Out Latitude', 'Check Out Longitude'
        ]
        
        # Create CSV
        csv_content = db.create_csv_string(data, headers)
        
        # Send as file
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = f"attendance_data_{start_date}_to_{end_date}.csv"
        
        await update.message.reply_document(
            document=csv_file,
            caption=f"📊 Detailed Attendance Export\n📅 {start_date} to {end_date}\n📁 {len(data)} records"
        )

    async def reminders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle reminder settings for employees"""
        user = update.effective_user
        
        if not db.is_employee_registered(user.id):
            await update.message.reply_text("❌ Please register first using /register")
            return
        
        keyboard = [
            [InlineKeyboardButton("⏰ Set Check-in Reminder", callback_data="set_checkin_reminder")],
            [InlineKeyboardButton("🔔 Set Check-out Reminder", callback_data="set_checkout_reminder")],
            [InlineKeyboardButton("🔇 Disable Reminders", callback_data="disable_reminders")],
            [InlineKeyboardButton("📊 View Settings", callback_data="view_reminder_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "⏰ **Reminder Settings**\n\n"
            "Manage your attendance reminders:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    async def set_reminder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set reminder time via command"""
        user = update.effective_user
        
        if not db.is_employee_registered(user.id):
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
            db.update_reminder_settings(user.id, reminder_time=time_str, reminder_enabled=True)
            await update.message.reply_text(f"✅ Check-in reminder set to {time_str}")
        elif reminder_type == "checkout":
            db.update_reminder_settings(user.id, checkout_reminder_time=time_str, checkout_reminder_enabled=True)
            await update.message.reply_text(f"✅ Check-out reminder set to {time_str}")
        else:
            await update.message.reply_text("❌ Invalid reminder type. Use 'checkin' or 'checkout'")

    async def admin_alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin alert settings"""
        user = update.effective_user
        
        if not db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        alert_enabled, late_threshold = db.get_admin_alert_settings(user.id)
        
        keyboard = [
            [InlineKeyboardButton("🔔 Enable Alerts" if not alert_enabled else "🔇 Disable Alerts", 
                                callback_data="toggle_admin_alerts")],
            [InlineKeyboardButton("⏱️ Set Late Threshold", callback_data="set_late_threshold")],
            [InlineKeyboardButton("📊 Test Alert", callback_data="test_admin_alert")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        status = "Enabled" if alert_enabled else "Disabled"
        await update.message.reply_text(
            f"🚨 **Admin Alert Settings**\n\n"
            f"Status: {status}\n"
            f"Late Threshold: {late_threshold} minutes\n\n"
            f"You will receive alerts for:\n"
            f"• Late check-ins\n"
            f"• Missed check-outs\n"
            f"• Attendance violations",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

    def run(self):
        """Start the bot with notification service"""
        print("🤖 Starting El Mansoura Attendance Bot...")
        print(f"🏢 Office Location: {OFFICE_LAT}, {OFFICE_LON}")
        print(f"📏 Attendance Radius: {OFFICE_RADIUS}m")
        print("🔔 Notification service enabled")
        
        # Start notification service in background
        asyncio.create_task(self.notification_service.run_scheduler())
        
        self.app.run_polling()

def main():
    """Main function"""
    if not BOT_TOKEN:
        print("❌ Error: BOT_TOKEN not found in environment variables!")
        print("Please add your bot token to the .env file")
        return
    
    bot = AttendanceBot()
    bot.run()

if __name__ == '__main__':
    main() 