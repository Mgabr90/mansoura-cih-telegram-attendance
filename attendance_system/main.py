"""
Main application module for the Enhanced Attendance System.

This module serves as the entry point for the Telegram bot application,
orchestrating all components and handling the application lifecycle.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from typing import Optional

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

from .core.config import Config
from .core.database import AttendanceDatabase
from .handlers.employee import EmployeeHandlers
from .handlers.admin import AdminHandlers
from .services.notification import NotificationService
from .services.health import HealthService
from .utils.messages import MessageFormatter

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, Config.LOG_LEVEL),
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('attendance_bot.log') if not Config.DEBUG else logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AttendanceBot:
    """
    Main attendance bot application class.
    
    Manages the entire bot lifecycle including initialization, configuration,
    handler registration, and graceful shutdown.
    """
    
    def __init__(self):
        """Initialize the attendance bot."""
        logger.info("Initializing Enhanced Attendance Bot...")
        
        # Validate configuration
        if not Config.is_valid():
            config_errors = Config.validate()
            raise ValueError(f"Invalid configuration: {', '.join(config_errors)}")
        
        # Initialize core components
        self.db = AttendanceDatabase()
        self.message_formatter = MessageFormatter()
        
        # Initialize handlers
        self.employee_handlers = EmployeeHandlers(self.db, self.message_formatter)
        self.admin_handlers = AdminHandlers(self.db, self.message_formatter)
        
        # Initialize services
        self.notification_service = NotificationService(Config.BOT_TOKEN, self.db, self.message_formatter)
        self.health_service = HealthService(self.db) if Config.SERVER_URL else None
        
        # Initialize Telegram application
        self.app = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
        
        # Register all handlers
        self._register_handlers()
        
        logger.info(f"Bot initialized successfully - {Config.get_summary()}")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, initiating graceful shutdown...")
            asyncio.create_task(self.shutdown())
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _register_handlers(self) -> None:
        """Register all command and message handlers."""
        # Employee commands
        self.app.add_handler(CommandHandler("start", self.employee_handlers.start_command))
        self.app.add_handler(CommandHandler("register", self.employee_handlers.register_command))
        self.app.add_handler(CommandHandler("status", self.employee_handlers.status_command))
        self.app.add_handler(CommandHandler("report", self.employee_handlers.report_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("myid", self.myid_command))
        
        # Admin commands
        self.app.add_handler(CommandHandler("admin", self.admin_handlers.admin_command))
        self.app.add_handler(CommandHandler("set_webhook", self.admin_handlers.set_webhook_command))
        self.app.add_handler(CommandHandler("webhook_info", self.admin_handlers.webhook_info_command))
        self.app.add_handler(CommandHandler("delete_webhook", self.admin_handlers.delete_webhook_command))
        self.app.add_handler(CommandHandler("add_admin", self.admin_handlers.add_admin_command))
        self.app.add_handler(CommandHandler("exceptional_hours", self.admin_handlers.exceptional_hours_command))
        self.app.add_handler(CommandHandler("admin_report", self.admin_handlers.admin_report_command))
        self.app.add_handler(CommandHandler("list_employees", self.admin_handlers.list_employees_command))
        self.app.add_handler(CommandHandler("server_status", self.admin_handlers.server_status_command))
        
        # Message handlers
        self.app.add_handler(MessageHandler(filters.CONTACT, self.employee_handlers.handle_contact))
        self.app.add_handler(MessageHandler(filters.LOCATION, self.employee_handlers.handle_location))
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.employee_handlers.handle_text_message
        ))
        
        # Callback query handler for inline keyboards
        self.app.add_handler(CallbackQueryHandler(self.admin_handlers.handle_callback_query))
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
        
        logger.info("All handlers registered successfully")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        user = update.effective_user
        is_admin = self.db.is_admin(user.id)
        is_registered = self.db.is_employee_registered(user.id)
        
        help_message = self.message_formatter.format_help_message(is_admin, is_registered)
        await update.message.reply_text(help_message, parse_mode='Markdown')
    
    async def myid_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /myid command."""
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
        """Global error handler."""
        logger.error("Exception while handling an update:", exc_info=context.error)
        
        # Log to database
        self.db.log_server_activity('error', f'Error: {str(context.error)}')
        
        # Try to notify user if possible
        if isinstance(update, Update) and update.effective_message:
            try:
                error_message = self.message_formatter.format_error_message("general")
                await update.effective_message.reply_text(error_message, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Failed to send error message to user: {e}")
    
    async def _send_startup_notification(self) -> None:
        """Send startup notification to admins."""
        try:
            admins = self.db.get_all_admins()
            if not admins:
                logger.info("No admins found for startup notification")
                return
            
            startup_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            config_summary = Config.get_summary()
            
            message = f"""
🚀 **Enhanced Attendance Bot Started**

⏰ **Startup Time:** {startup_time}
🌍 **Timezone:** {Config.TIMEZONE}
📍 **Office Location:** {config_summary['office_location']}

🔧 **Active Features:**
✅ Location-only attendance (manual entry disabled)
✅ Late/early reason prompts
✅ Exceptional working hours support
✅ Daily summary reports (8 PM)
✅ Enhanced admin controls
{f"✅ Server wake-up system" if Config.ENABLE_SERVER_WAKEUP else "❌ Server wake-up disabled"}

🖥️ **System Status:** Ready for attendance tracking! 🎯
"""
            
            for admin_id in admins:
                try:
                    await self.app.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    logger.info(f"Startup notification sent to admin {admin_id}")
                except Exception as e:
                    logger.error(f"Failed to send startup notification to admin {admin_id}: {e}")
            
            # Log startup
            self.db.log_server_activity('bot_startup', 'Enhanced bot started successfully')
            
        except Exception as e:
            logger.error(f"Error sending startup notifications: {e}")
    
    async def run(self) -> None:
        """Run the bot application."""
        try:
            # Initialize application
            await self.app.initialize()
            logger.info("Application initialized")
            
            # Start health service if configured
            if self.health_service:
                await self.health_service.start()
                logger.info("Health service started")
            
            # Send startup notification
            await self._send_startup_notification()
            
            # Start notification service
            notification_task = asyncio.create_task(
                self.notification_service.run_scheduler()
            )
            logger.info("Notification service started")
            
            # Start the bot
            await self.app.start()
            logger.info("Bot started - accepting updates")
            
            # Start polling
            await self.app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
            logger.info("🤖 Enhanced Attendance Bot is running!")
            logger.info(f"✅ Security features: Location-only attendance enforced")
            logger.info(f"✅ Admin features: Enhanced reporting and management")
            logger.info(f"✅ Employee features: Automated reason prompts")
            
            # Keep running until shutdown
            try:
                await notification_task
            except asyncio.CancelledError:
                logger.info("Notification task cancelled")
            
        except Exception as e:
            logger.error(f"Error running bot: {e}")
            raise
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the bot."""
        logger.info("Starting graceful shutdown...")
        
        try:
            # Stop health service
            if self.health_service:
                await self.health_service.stop()
                logger.info("Health service stopped")
            
            # Stop the bot
            if self.app.updater.running:
                await self.app.updater.stop()
                logger.info("Updater stopped")
            
            if self.app.running:
                await self.app.stop()
                logger.info("Application stopped")
            
            await self.app.shutdown()
            logger.info("Application shutdown complete")
            
            # Log shutdown
            self.db.log_server_activity('bot_shutdown', 'Bot shutdown gracefully')
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        logger.info("Shutdown complete")


async def main() -> None:
    """Main entry point for the application."""
    try:
        # Create and run bot
        bot = AttendanceBot()
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


def run_bot() -> None:
    """Synchronous entry point for running the bot."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Application failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    run_bot() 