import os
import sys
import logging
import asyncio
from datetime import datetime
import pytz
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Add current directory to path to fix imports
sys.path.append(os.path.dirname(__file__))

from database_enhanced import EnhancedAttendanceDatabase
from handlers.enhanced_employee_handlers import EnhancedEmployeeHandlers
from handlers.admin_handlers import AdminHandlers
from enhanced_notification_service import EnhancedNotificationService
from health_endpoint import start_health_server_thread

# Import config from renamed file to avoid directory conflict
from bot_config import Config

# Load environment variables from parent directory
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class EnhancedAttendanceBot:
    def __init__(self):
        # Validate configuration
        if not Config.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        
        # Initialize database
        self.db = EnhancedAttendanceDatabase()
        logger.info("Enhanced database initialized")
        
        # Initialize handlers
        self.employee_handlers = EnhancedEmployeeHandlers(self.db)
        self.admin_handlers = AdminHandlers(self.db)
        
        # Initialize notification service
        self.notification_service = EnhancedNotificationService(Config.BOT_TOKEN, self.db)
        
        # Initialize telegram application
        self.app = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Setup handlers
        self.setup_handlers()
        
        # Start health server for wake-up functionality
        self.health_thread = start_health_server_thread(port=int(os.getenv('PORT', 8080)))
        logger.info("Health server started for server wake-up functionality")
        
    def setup_handlers(self):
        """Setup all command and message handlers"""
        
        # Employee commands
        self.app.add_handler(CommandHandler("start", self.employee_handlers.start_command))
        self.app.add_handler(CommandHandler("register", self.employee_handlers.register_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("myid", self.myid_command))
        
        # Admin commands
        self.app.add_handler(CommandHandler("add_admin", self.admin_handlers.add_admin_command))
        self.app.add_handler(CommandHandler("exceptional_hours", self.admin_handlers.exceptional_hours_command))
        self.app.add_handler(CommandHandler("admin_report", self.admin_handlers.admin_report_command))
        self.app.add_handler(CommandHandler("list_employees", self.admin_handlers.list_employees_command))
        self.app.add_handler(CommandHandler("server_status", self.admin_handlers.server_status_command))
        
        # Message handlers
        self.app.add_handler(MessageHandler(filters.CONTACT, self.employee_handlers.handle_contact))
        self.app.add_handler(MessageHandler(filters.LOCATION, self.employee_handlers.handle_location))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.employee_handlers.handle_text_message))
        
        # Callback query handler for inline keyboards
        self.app.add_handler(CallbackQueryHandler(self.admin_handlers.handle_callback_query))
        
        logger.info("All handlers registered successfully")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        user = update.effective_user
        is_admin = self.db.is_admin(user.id)
        is_registered = self.db.is_employee_registered(user.id)
        
        help_text = """
🤖 **Enhanced Attendance System**

**🔒 Security Features:**
📍 Location sharing is MANDATORY
🚫 Manual location entry is DISABLED
✅ Must be within 100m of El Mansoura office

**👤 Employee Commands:**
"""
        
        if not is_registered:
            help_text += """
📝 `/register` - Register as an employee
⚠️ You must register before using the system
"""
        else:
            help_text += """
📊 Use buttons to check status and reports
🟢 Use "Check In" button with location
🔴 Use "Check Out" button with location
📝 Late check-ins require a reason
📝 Early check-outs require a reason
"""
        
        help_text += """
🆔 `/myid` - Get your Telegram user ID
ℹ️ `/help` - Show this help message

**⏰ Working Hours:**
🏢 Standard: 09:00 - 17:00
📅 Exceptional hours may apply for specific dates

**📍 Office Location:**
🏢 29R3+7Q El Mansoura 1
📏 100m radius requirement
"""
        
        if is_admin:
            help_text += """

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
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def myid_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /myid command"""
        user = update.effective_user
        await update.message.reply_text(
            f"🆔 **Your Telegram ID**\n\n"
            f"User ID: `{user.id}`\n"
            f"Username: @{user.username or 'None'}\n"
            f"First Name: {user.first_name}\n\n"
            f"💡 Share this ID with admins if needed.",
            parse_mode='Markdown'
        )
    
    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors"""
        logger.error("Exception while handling an update:", exc_info=context.error)
        
        # Log to database
        self.db.log_server_activity('error', f'Error: {str(context.error)}')
        
        # Try to notify user if possible
        if isinstance(update, Update) and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "⚠️ **System Error**\n\n"
                    "An unexpected error occurred. Please try again.\n"
                    "If the problem persists, contact an administrator.",
                    parse_mode='Markdown'
                )
            except Exception:
                pass  # Ignore if we can't send error message
    
    async def startup_message(self):
        """Send startup message to admins"""
        try:
            admins = self.db.get_all_admins_for_daily_summary()
            egypt_tz = pytz.timezone(Config.TIMEZONE)
            startup_time = datetime.now(egypt_tz)
            
            message = f"""
🚀 **Enhanced Attendance Bot Started**

⏰ Startup Time: {startup_time.strftime('%Y-%m-%d %H:%M:%S')}
🌍 Timezone: Africa/Cairo
📍 Location: El Mansoura, Egypt

🔧 **New Features Active:**
✅ Location-only attendance (manual entry disabled)
✅ Late/early reason prompts
✅ Exceptional working hours support
✅ Daily summary reports (8 PM)
✅ Server wake-up system
✅ Enhanced admin controls

🖥️ Health endpoint: /health
📊 Status endpoint: /status

System is ready for attendance tracking! 🎯
"""
            
            for admin_id in admins:
                try:
                    await self.app.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    logger.error(f"Failed to send startup message to admin {admin_id}: {e}")
            
            # Log startup
            self.db.log_server_activity('bot_startup', 'Enhanced bot started successfully')
            
        except Exception as e:
            logger.error(f"Error sending startup messages: {e}")
    
    async def run_bot(self):
        """Run the bot"""
        # Add error handler
        self.app.add_error_handler(self.error_handler)
        
        # Initialize bot
        await self.app.initialize()
        
        # Send startup message
        await self.startup_message()
        
        # Start notification scheduler in background
        notification_task = asyncio.create_task(
            self.notification_service.run_enhanced_scheduler()
        )
        
        logger.info("Starting enhanced attendance bot...")
        logger.info("✅ Location-only attendance enforced")
        logger.info("✅ Late/early reason prompts enabled")
        logger.info("✅ Exceptional hours support active")
        logger.info("✅ Daily summaries scheduled for 8 PM")
        logger.info("✅ Server wake-up system running")
        
        # Start polling
        await self.app.start()
        await self.app.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        
        try:
            # Keep running
            await asyncio.gather(notification_task)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        finally:
            # Cleanup
            await self.app.stop()
            await self.app.shutdown()
            notification_task.cancel()

def main():
    """Main entry point"""
    try:
        # Create and run bot
        bot = EnhancedAttendanceBot()
        asyncio.run(bot.run_bot())
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise

if __name__ == '__main__':
    main() 