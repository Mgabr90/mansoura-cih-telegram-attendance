#!/usr/bin/env python3
"""
El Mansoura Attendance Bot - Main Entry Point
==============================================

A modular, enterprise-grade attendance tracking system for Telegram.
"""

import logging
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from config.settings import BOT_TOKEN, DATABASE_NAME, OFFICE_LATITUDE, OFFICE_LONGITUDE, OFFICE_RADIUS, validate_settings
from database import AttendanceDatabase
from notification_service import NotificationService
from handlers.employee_handlers import EmployeeHandlers
from handlers.admin_handlers import AdminHandlers

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class AttendanceBot:
    """Main bot orchestrator that coordinates all handlers and services"""
    
    def __init__(self):
        # Validate configuration
        validate_settings()
        
        # Initialize core services
        self.db = AttendanceDatabase(DATABASE_NAME)
        self.notification_service = NotificationService(BOT_TOKEN, self.db)
        
        # Initialize handlers
        self.employee_handlers = EmployeeHandlers(self.db)
        self.admin_handlers = AdminHandlers(self.db)
        
        # Initialize Telegram application
        self.app = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup all command and message handlers"""
        
        # Employee handlers
        self.app.add_handler(CommandHandler("start", self.employee_handlers.start_command))
        self.app.add_handler(CommandHandler("help", self.employee_handlers.help_command))
        self.app.add_handler(CommandHandler("register", self.employee_handlers.register_command))
        self.app.add_handler(CommandHandler("status", self.employee_handlers.status_command))
        self.app.add_handler(CommandHandler("report", self.employee_handlers.report_command))
        
        # Admin handlers
        self.app.add_handler(CommandHandler("admin", self.admin_handlers.admin_command))
        self.app.add_handler(CommandHandler("add_admin", self.admin_handlers.add_admin_command))
        self.app.add_handler(CommandHandler("all_report", self.admin_handlers.all_report_command))
        self.app.add_handler(CommandHandler("admin_alerts", self.admin_handlers.admin_alerts_command))
        
        # Message handlers
        self.app.add_handler(MessageHandler(filters.CONTACT, self.employee_handlers.handle_contact))
        self.app.add_handler(MessageHandler(filters.LOCATION, self.employee_handlers.handle_location))
        
        # Callback query handler
        self.app.add_handler(CallbackQueryHandler(self.handle_callbacks))
    
    async def handle_callbacks(self, update, context):
        """Centralized callback query handler"""
        query = update.callback_query
        user = update.effective_user
        
        await query.answer()
        
        # Route to appropriate handler based on callback data
        if query.data.startswith("admin_"):
            result = await self.admin_handlers.handle_admin_callbacks(query, user)
            if result == "all_report":
                await self.admin_handlers.all_report_command(update, context)
        
        # Add more routing logic for other handlers here
    
    async def start_notification_service(self):
        """Start the background notification service"""
        try:
            await self.notification_service.run_scheduler()
        except Exception as e:
            logger.error(f"Notification service error: {e}")
    
    def run(self):
        """Start the bot with all services"""
        logger.info("🤖 Starting El Mansoura Attendance Bot...")
        logger.info(f"🏢 Office Location: {OFFICE_LATITUDE}, {OFFICE_LONGITUDE}")
        logger.info(f"📏 Attendance Radius: {OFFICE_RADIUS}m")
        logger.info(f"🗄️ Database: {DATABASE_NAME}")
        logger.info("🔔 Notification service enabled")
        logger.info("🎯 Modular architecture loaded")
        
        # Start notification service in background
        asyncio.create_task(self.start_notification_service())
        
        # Start the bot
        self.app.run_polling()

def main():
    """Main entry point"""
    try:
        bot = AttendanceBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        raise

if __name__ == '__main__':
    main() 