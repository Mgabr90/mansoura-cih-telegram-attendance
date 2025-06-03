#!/usr/bin/env python3
"""
El Mansoura Attendance Bot - Modular Version
A comprehensive Telegram bot for employee attendance tracking with location verification.
"""

import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

# Import configuration
from config.settings import BOT_TOKEN, validate_settings

# Import database and services
from database import AttendanceDatabase
from notification_service import NotificationService

# Import modular handlers
from handlers.employee_handlers import EmployeeHandlers
from handlers.admin_handlers import AdminHandlers
from handlers.export_handlers import ExportHandlers
from services.callback_service import CallbackService

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AttendanceBot:
    """Main bot class that orchestrates all components"""
    
    def __init__(self):
        # Validate settings first
        validate_settings()
        
        # Initialize core components
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.db = AttendanceDatabase()
        self.notification_service = NotificationService(BOT_TOKEN, self.db)
        
        # Initialize handler classes
        self.employee_handlers = EmployeeHandlers(self.db)
        self.admin_handlers = AdminHandlers(self.db)
        self.export_handlers = ExportHandlers(self.db)
        self.callback_service = CallbackService(self.db)
        
        # Setup all handlers
        self.setup_handlers()
    
    def setup_handlers(self):
        """Register all command and message handlers"""
        # Employee commands
        self.app.add_handler(CommandHandler("start", self.employee_handlers.start_command))
        self.app.add_handler(CommandHandler("register", self.employee_handlers.register_command))
        self.app.add_handler(CommandHandler("status", self.employee_handlers.status_command))
        self.app.add_handler(CommandHandler("report", self.employee_handlers.report_command))
        self.app.add_handler(CommandHandler("reminders", self.employee_handlers.reminders_command))
        self.app.add_handler(CommandHandler("set_reminder", self.employee_handlers.set_reminder_command))
        
        # Admin commands
        self.app.add_handler(CommandHandler("admin", self.admin_handlers.admin_command))
        self.app.add_handler(CommandHandler("add_admin", self.admin_handlers.add_admin_command))
        self.app.add_handler(CommandHandler("all_report", self.admin_handlers.all_report_command))
        self.app.add_handler(CommandHandler("admin_alerts", self.admin_handlers.admin_alerts_command))
        
        # Export commands (admin only)
        self.app.add_handler(CommandHandler("export_daily", self.export_handlers.export_daily_command))
        self.app.add_handler(CommandHandler("export_monthly", self.export_handlers.export_monthly_command))
        self.app.add_handler(CommandHandler("export_employees", self.export_handlers.export_employees_command))
        self.app.add_handler(CommandHandler("export_attendance", self.export_handlers.export_attendance_command))
        
        # Help command (shared)
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Message handlers
        self.app.add_handler(MessageHandler(filters.LOCATION, self.employee_handlers.handle_location))
        self.app.add_handler(MessageHandler(filters.CONTACT, self.employee_handlers.handle_contact))
        
        # Callback query handler
        self.app.add_handler(CallbackQueryHandler(self.callback_service.handle_callback))
    
    async def help_command(self, update, context):
        """Centralized help command"""
        user = update.effective_user
        is_admin = self.db.is_admin(user.id) if self.db.is_employee_registered(user.id) else False
        
        help_text = """
🤖 **El Mansoura Attendance Bot Help**

**Available Commands:**
• `/start` - Start the bot and see main menu
• `/register` - Register as an employee
• `/status` - Check your current attendance status
• `/report` - Get your attendance report (last 7 days)
• `/reminders` - Manage attendance reminders
• `/set_reminder checkin HH:MM` - Set check-in reminder
• `/set_reminder checkout HH:MM` - Set check-out reminder
• `/help` - Show this help message

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
    
    def run(self):
        """Start the bot with all services"""
        logger.info("🤖 Starting El Mansoura Attendance Bot (Modular Version)...")
        logger.info("🔔 Notification service enabled")
        logger.info("📊 All handlers registered")
        
        # Start notification service in background
        asyncio.create_task(self.notification_service.run_scheduler())
        
        # Run the bot
        self.app.run_polling()

def main():
    """Main function"""
    try:
        bot = AttendanceBot()
        bot.run()
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        print(f"❌ Configuration Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    main() 