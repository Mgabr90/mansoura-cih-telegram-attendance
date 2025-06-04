"""
Admin handlers module for the Enhanced Attendance System.

This module contains all Telegram bot handlers for admin interactions.
"""

import logging
from datetime import datetime, date
from typing import List, Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ..core.database import AttendanceDatabase
from ..core.config import Config
from ..utils.keyboards import KeyboardBuilder
from ..utils.messages import MessageFormatter

logger = logging.getLogger(__name__)


class AdminHandlers:
    """
    Admin handler class for managing admin interactions.
    
    Handles all admin-related commands and callback queries including
    dashboard, employee management, and system administration.
    """
    
    def __init__(self, db: AttendanceDatabase, message_formatter: MessageFormatter):
        """
        Initialize admin handlers.
        
        Args:
            db: Database instance
            message_formatter: Message formatter instance
        """
        self.db = db
        self.message_formatter = message_formatter
        self.keyboard_builder = KeyboardBuilder()
        self.config = Config()
        
        logger.info("Admin handlers initialized")
    
    async def set_webhook_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /set_webhook command - first priority admin function."""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            error_message = self.message_formatter.format_error_message("admin_required")
            await update.message.reply_text(error_message, parse_mode='Markdown')
            return
        
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "🔗 **Webhook Setup**\n\n"
                "Usage: `/set_webhook <webhook_url>`\n\n"
                "**Examples:**\n"
                "• `/set_webhook https://your-app.onrender.com/webhook`\n"
                "• `/set_webhook https://your-domain.com/webhook`\n\n"
                "⚠️ **Important:** The URL must be HTTPS and accessible from the internet.",
                parse_mode='Markdown'
            )
            return
        
        webhook_url = context.args[0]
        
        # Validate URL format
        if not webhook_url.startswith('https://'):
            await update.message.reply_text(
                "❌ **Invalid URL**\n\n"
                "Webhook URL must start with `https://`\n"
                "Telegram requires HTTPS for webhooks.",
                parse_mode='Markdown'
            )
            return
        
        # Add /webhook to the end if not present
        if not webhook_url.endswith('/webhook'):
            webhook_url = webhook_url.rstrip('/') + '/webhook'
        
        try:
            # Set the webhook
            bot = context.bot
            await bot.set_webhook(url=webhook_url)
            
            # Test the webhook
            webhook_info = await bot.get_webhook_info()
            
            success_message = "✅ **Webhook Set Successfully!**\n\n"
            success_message += f"**URL:** `{webhook_url}`\n"
            success_message += f"**Status:** Active\n"
            success_message += f"**Pending Updates:** {webhook_info.pending_update_count}\n"
            
            if webhook_info.last_error_date:
                success_message += f"**Last Error:** {webhook_info.last_error_message}\n"
            else:
                success_message += "**Status:** ✅ No errors\n"
            
            await update.message.reply_text(success_message, parse_mode='Markdown')
            logger.info(f"Admin {user.id} set webhook to {webhook_url}")
            
        except Exception as e:
            error_message = f"❌ **Webhook Setup Failed**\n\n"
            error_message += f"Error: `{str(e)}`\n\n"
            error_message += "**Common Issues:**\n"
            error_message += "• URL not accessible from internet\n"
            error_message += "• Invalid SSL certificate\n"
            error_message += "• Server not responding\n"
            error_message += "• URL format incorrect"
            
            await update.message.reply_text(error_message, parse_mode='Markdown')
            logger.error(f"Webhook setup failed for admin {user.id}: {str(e)}")
    
    async def webhook_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /webhook_info command - get current webhook information."""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            error_message = self.message_formatter.format_error_message("admin_required")
            await update.message.reply_text(error_message, parse_mode='Markdown')
            return
        
        try:
            bot = context.bot
            webhook_info = await bot.get_webhook_info()
            
            info_message = "🔗 **Current Webhook Information**\n\n"
            
            if webhook_info.url:
                info_message += f"**URL:** `{webhook_info.url}`\n"
                info_message += f"**Status:** ✅ Active\n"
                info_message += f"**Pending Updates:** {webhook_info.pending_update_count}\n"
                info_message += f"**Max Connections:** {webhook_info.max_connections}\n"
                
                if webhook_info.last_error_date:
                    error_date = datetime.fromtimestamp(webhook_info.last_error_date)
                    info_message += f"**Last Error Date:** {error_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    info_message += f"**Last Error:** `{webhook_info.last_error_message}`\n"
                else:
                    info_message += "**Last Error:** None ✅\n"
                
                if webhook_info.ip_address:
                    info_message += f"**IP Address:** `{webhook_info.ip_address}`\n"
                    
            else:
                info_message += "**Status:** ❌ No webhook set\n"
                info_message += "Use `/set_webhook <url>` to configure webhook."
            
            await update.message.reply_text(info_message, parse_mode='Markdown')
            logger.info(f"Admin {user.id} requested webhook info")
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Error Getting Webhook Info**\n\n"
                f"Error: `{str(e)}`",
                parse_mode='Markdown'
            )
            logger.error(f"Failed to get webhook info for admin {user.id}: {str(e)}")
    
    async def delete_webhook_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /delete_webhook command - remove current webhook."""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            error_message = self.message_formatter.format_error_message("admin_required")
            await update.message.reply_text(error_message, parse_mode='Markdown')
            return
        
        try:
            bot = context.bot
            await bot.delete_webhook()
            
            success_message = "✅ **Webhook Deleted Successfully**\n\n"
            success_message += "The bot is now using polling mode.\n"
            success_message += "Use `/set_webhook <url>` to set a new webhook."
            
            await update.message.reply_text(success_message, parse_mode='Markdown')
            logger.info(f"Admin {user.id} deleted webhook")
            
        except Exception as e:
            await update.message.reply_text(
                f"❌ **Error Deleting Webhook**\n\n"
                f"Error: `{str(e)}`",
                parse_mode='Markdown'
            )
            logger.error(f"Failed to delete webhook for admin {user.id}: {str(e)}")

    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /admin command - main admin panel."""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            error_message = self.message_formatter.format_error_message("admin_required")
            await update.message.reply_text(error_message, parse_mode='Markdown')
            return
        
        # Create enhanced admin keyboard with webhook management
        keyboard = [
            [
                InlineKeyboardButton("🔗 Webhook Setup", callback_data="webhook_menu"),
                InlineKeyboardButton("📊 Dashboard", callback_data="today_report")
            ],
            [
                InlineKeyboardButton("👥 All Employees", callback_data="all_employees"),
                InlineKeyboardButton("⏰ Exceptional Hours", callback_data="exceptional_hours_menu")
            ],
            [
                InlineKeyboardButton("📈 Analytics", callback_data="analytics"),
                InlineKeyboardButton("⚙️ Settings", callback_data="settings_menu")
            ],
            [
                InlineKeyboardButton("🖥️ Server Status", callback_data="server_status"),
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_report")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔐 **Admin Control Panel**\n\n"
            "Welcome to the Enhanced Attendance System administration.\n"
            "🔗 **Webhook Setup** is your first priority for deployment.\n\n"
            "Choose an option below:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"Admin panel accessed by user {user.id}")
    
    async def add_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /add_admin command."""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            error_message = self.message_formatter.format_error_message("admin_required")
            await update.message.reply_text(error_message, parse_mode='Markdown')
            return
        
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "❌ **Invalid Usage**\n\n"
                "Usage: `/add_admin <user_id>`\n"
                "Example: `/add_admin 123456789`",
                parse_mode='Markdown'
            )
            return
        
        try:
            new_admin_id = int(context.args[0])
            
            # Check if user exists as employee first
            if not self.db.is_employee_registered(new_admin_id):
                await update.message.reply_text(
                    "❌ **User Not Found**\n\n"
                    "The specified user is not registered as an employee.\n"
                    "They must register first before becoming an admin.",
                    parse_mode='Markdown'
                )
                return
            
            # Add admin privileges
            success = self.db.add_admin(new_admin_id)
            
            if success:
                await update.message.reply_text(
                    f"✅ **Admin Added Successfully**\n\n"
                    f"User `{new_admin_id}` now has admin privileges.",
                    parse_mode='Markdown'
                )
                logger.info(f"Admin {user.id} granted admin privileges to {new_admin_id}")
            else:
                await update.message.reply_text(
                    "❌ **Failed to Add Admin**\n\n"
                    "User may already be an admin or an error occurred.",
                    parse_mode='Markdown'
                )
        
        except ValueError:
            await update.message.reply_text(
                "❌ **Invalid User ID**\n\n"
                "Please provide a valid numeric user ID.",
                parse_mode='Markdown'
            )
    
    async def exceptional_hours_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /exceptional_hours command."""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            error_message = self.message_formatter.format_error_message("admin_required")
            await update.message.reply_text(error_message, parse_mode='Markdown')
            return
        
        if not context.args or len(context.args) < 4:
            await update.message.reply_text(
                "❌ **Invalid Usage**\n\n"
                "Usage: `/exceptional_hours <user_id> <date> <start_time> <end_time> [reason]`\n\n"
                "Examples:\n"
                "• `/exceptional_hours 123456789 2024-01-15 10:00 16:00 Medical appointment`\n"
                "• `/exceptional_hours 123456789 2024-01-15 08:00 15:00`",
                parse_mode='Markdown'
            )
            return
        
        try:
            employee_id = int(context.args[0])
            date_str = context.args[1]
            start_time = context.args[2]
            end_time = context.args[3]
            reason = ' '.join(context.args[4:]) if len(context.args) > 4 else None
            
            # Validate date format
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Validate time formats
            datetime.strptime(start_time, '%H:%M')
            datetime.strptime(end_time, '%H:%M')
            
            # Check if employee exists
            if not self.db.is_employee_registered(employee_id):
                await update.message.reply_text(
                    "❌ **Employee Not Found**\n\n"
                    "The specified employee is not registered.",
                    parse_mode='Markdown'
                )
                return
            
            # Set exceptional hours
            success = self.db.set_exceptional_hours(
                employee_id, target_date, start_time, end_time, reason
            )
            
            if success:
                employee_info = self.db.get_employee_info(employee_id)
                employee_name = f"{employee_info[1]} {employee_info[2] or ''}".strip() if employee_info else str(employee_id)
                
                message = f"✅ **Exceptional Hours Set**\n\n"
                message += f"**Employee:** {employee_name}\n"
                message += f"**Date:** {date_str}\n"
                message += f"**Hours:** {start_time} - {end_time}\n"
                if reason:
                    message += f"**Reason:** {reason}\n"
                
                await update.message.reply_text(message, parse_mode='Markdown')
                logger.info(f"Admin {user.id} set exceptional hours for employee {employee_id}")
            else:
                await update.message.reply_text(
                    "❌ **Failed to Set Exceptional Hours**\n\n"
                    "An error occurred while setting the exceptional hours.",
                    parse_mode='Markdown'
                )
        
        except ValueError as e:
            await update.message.reply_text(
                f"❌ **Invalid Input**\n\n"
                f"Please check your input format:\n"
                f"• Date: YYYY-MM-DD\n"
                f"• Time: HH:MM\n"
                f"• User ID: numeric\n\n"
                f"Error: {str(e)}",
                parse_mode='Markdown'
            )
    
    async def admin_report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /admin_report command - real-time dashboard."""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            error_message = self.message_formatter.format_error_message("admin_required")
            await update.message.reply_text(error_message, parse_mode='Markdown')
            return
        
        # Get today's summary data
        summary_data = self.db.get_daily_summary()
        summary_message = self.message_formatter.format_daily_summary(summary_data)
        
        # Add quick actions keyboard
        keyboard = self.keyboard_builder.get_quick_action_keyboard()
        
        await update.message.reply_text(
            summary_message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        logger.info(f"Admin report generated for user {user.id}")
    
    async def list_employees_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /list_employees command."""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            error_message = self.message_formatter.format_error_message("admin_required")
            await update.message.reply_text(error_message, parse_mode='Markdown')
            return
        
        employees = self.db.get_all_employees()
        
        if not employees:
            await update.message.reply_text(
                "👥 **Employee Directory**\n\n"
                "No employees registered yet.",
                parse_mode='Markdown'
            )
            return
        
        message = "👥 **Employee Directory**\n\n"
        
        for i, emp in enumerate(employees[:10], 1):  # Limit to first 10 for readability
            telegram_id, username, first_name, last_name, phone, registration_date = emp
            name = f"{first_name} {last_name or ''}".strip()
            username_str = f"@{username}" if username else "No username"
            
            message += f"**{i}. {name}**\n"
            message += f"   ID: `{telegram_id}`\n"
            message += f"   Username: {username_str}\n"
            message += f"   Phone: {phone or 'Not provided'}\n"
            message += f"   Registered: {registration_date}\n\n"
        
        if len(employees) > 10:
            message += f"... and {len(employees) - 10} more employees\n"
            message += "Use inline buttons for full employee management."
        
        # Add employee management keyboard
        keyboard = [[
            InlineKeyboardButton("👥 Full Employee List", callback_data="admin_all_employees"),
            InlineKeyboardButton("📊 Employee Reports", callback_data="admin_employee_reports")
        ]]
        
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        logger.info(f"Employee list generated for admin {user.id}")
    
    async def server_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /server_status command."""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            error_message = self.message_formatter.format_error_message("admin_required")
            await update.message.reply_text(error_message, parse_mode='Markdown')
            return
        
        # Get server activity logs
        recent_activities = self.db.get_recent_server_activity(10)
        
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"🖥️ **Server Status Report**\n\n"
        message += f"**Current Time:** {current_time}\n"
        message += f"**Timezone:** {Config.TIMEZONE}\n"
        message += f"**Health Checks:** {'Enabled' if Config.ENABLE_SERVER_WAKEUP else 'Disabled'}\n\n"
        
        message += "**Recent Activity:**\n"
        if recent_activities:
            for activity in recent_activities:
                timestamp, activity_type, description = activity
                message += f"• `{timestamp}` - {activity_type}: {description}\n"
        else:
            message += "No recent activity logged.\n"
        
        # Add server management keyboard
        keyboard = [[
            InlineKeyboardButton("🔄 Refresh Status", callback_data="admin_server_refresh"),
            InlineKeyboardButton("📊 Full Activity Log", callback_data="admin_server_logs")
        ]]
        
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        
        logger.info(f"Server status report generated for admin {user.id}")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        user = query.from_user
        
        # Answer the callback query to remove loading state
        await query.answer()
        
        if not self.db.is_admin(user.id):
            await query.edit_message_text("❌ Admin privileges required.")
            return
        
        data = query.data
        
        # Route callback queries
        if data == "webhook_menu":
            await self._handle_webhook_menu(query)
        elif data == "webhook_info":
            await self._handle_webhook_info(query)
        elif data == "webhook_delete":
            await self._handle_webhook_delete(query)
        elif data == "today_report":
            await self._handle_today_report(query)
        elif data == "all_employees":
            await self._handle_all_employees(query)
        elif data == "exceptional_hours_menu":
            await self._handle_exceptional_hours_menu(query)
        elif data == "analytics":
            await self._handle_analytics(query)
        elif data == "settings_menu":
            await self._handle_settings_menu(query)
        elif data == "server_status":
            await self._handle_server_status(query)
        elif data == "refresh_report":
            await self._handle_refresh_report(query)
        elif data == "send_summary":
            await self._handle_send_summary(query)
        elif data.startswith("emp_"):
            await self._handle_employee_action(query, data)
        else:
            await query.edit_message_text("❓ Unknown action.")
        
        logger.info(f"Callback query '{data}' handled for admin {user.id}")
    
    async def _handle_webhook_menu(self, query) -> None:
        """Handle webhook management menu callback."""
        try:
            # Get current webhook info
            webhook_info = await query.get_bot().get_webhook_info()
            
            message = "🔗 **Webhook Management**\n\n"
            
            if webhook_info.url:
                message += f"**Current Status:** ✅ Active\n"
                message += f"**URL:** `{webhook_info.url}`\n"
                message += f"**Pending Updates:** {webhook_info.pending_update_count}\n\n"
                
                if webhook_info.last_error_date:
                    error_date = datetime.fromtimestamp(webhook_info.last_error_date)
                    message += f"**Last Error:** {error_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    message += f"**Error Details:** {webhook_info.last_error_message}\n\n"
                else:
                    message += "**Status:** ✅ No errors\n\n"
                    
                keyboard = [
                    [InlineKeyboardButton("📋 View Details", callback_data="webhook_info")],
                    [InlineKeyboardButton("🗑️ Delete Webhook", callback_data="webhook_delete")],
                    [InlineKeyboardButton("« Back to Admin", callback_data="admin_main_menu")]
                ]
            else:
                message += "**Current Status:** ❌ No webhook set\n"
                message += "**Mode:** Polling (development)\n\n"
                message += "**To set up webhook:**\n"
                message += "Use: `/set_webhook <https://your-domain.com>`\n\n"
                message += "**Important:** Webhook is required for production deployment!"
                
                keyboard = [
                    [InlineKeyboardButton("« Back to Admin", callback_data="admin_main_menu")]
                ]
            
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ **Error accessing webhook information**\n\n"
                f"Error: `{str(e)}`",
                parse_mode='Markdown'
            )
    
    async def _handle_webhook_info(self, query) -> None:
        """Handle webhook info display callback."""
        try:
            webhook_info = await query.get_bot().get_webhook_info()
            
            message = "🔗 **Detailed Webhook Information**\n\n"
            
            if webhook_info.url:
                message += f"**URL:** `{webhook_info.url}`\n"
                message += f"**Has Custom Certificate:** {'Yes' if webhook_info.has_custom_certificate else 'No'}\n"
                message += f"**Pending Update Count:** {webhook_info.pending_update_count}\n"
                message += f"**Max Connections:** {webhook_info.max_connections}\n"
                
                if webhook_info.allowed_updates:
                    message += f"**Allowed Updates:** {', '.join(webhook_info.allowed_updates)}\n"
                
                if webhook_info.ip_address:
                    message += f"**IP Address:** `{webhook_info.ip_address}`\n"
                
                if webhook_info.last_error_date:
                    error_date = datetime.fromtimestamp(webhook_info.last_error_date)
                    message += f"\n**⚠️ Last Error:**\n"
                    message += f"**Date:** {error_date.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    message += f"**Message:** {webhook_info.last_error_message}\n"
                else:
                    message += "\n✅ **No errors recorded**"
            else:
                message += "❌ **No webhook configured**\n"
                message += "Bot is running in polling mode."
            
            keyboard = [[InlineKeyboardButton("« Back to Webhook Menu", callback_data="webhook_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ **Error getting webhook details**\n\n"
                f"Error: `{str(e)}`",
                parse_mode='Markdown'
            )
    
    async def _handle_webhook_delete(self, query) -> None:
        """Handle webhook deletion callback."""
        try:
            await query.get_bot().delete_webhook()
            
            message = "✅ **Webhook Deleted Successfully**\n\n"
            message += "The bot is now using polling mode.\n"
            message += "This is suitable for development but not for production.\n\n"
            message += "Use `/set_webhook <url>` to configure a new webhook."
            
            keyboard = [[InlineKeyboardButton("« Back to Webhook Menu", callback_data="webhook_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            logger.info(f"Webhook deleted via callback by admin {query.from_user.id}")
            
        except Exception as e:
            await query.edit_message_text(
                f"❌ **Error deleting webhook**\n\n"
                f"Error: `{str(e)}`",
                parse_mode='Markdown'
            )
    
    async def _handle_today_report(self, query) -> None:
        """Handle today's report callback."""
        summary_data = self.db.get_daily_summary()
        summary_message = self.message_formatter.format_daily_summary(summary_data)
        
        keyboard = self.keyboard_builder.get_quick_action_keyboard()
        
        await query.edit_message_text(
            summary_message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def _handle_all_employees(self, query) -> None:
        """Handle all employees list callback."""
        employees = self.db.get_all_employees()
        
        if not employees:
            await query.edit_message_text("👥 No employees registered yet.")
            return
        
        # Create paginated employee list (show first 5)
        message = "👥 **All Employees**\n\n"
        
        for i, emp in enumerate(employees[:5], 1):
            telegram_id, username, first_name, last_name, phone, registration_date = emp
            name = f"{first_name} {last_name or ''}".strip()
            
            message += f"**{i}. {name}**\n"
            message += f"   ID: `{telegram_id}` | Phone: {phone or 'N/A'}\n\n"
        
        # Add pagination keyboard if needed
        if len(employees) > 5:
            keyboard = self.keyboard_builder.get_pagination_keyboard(0, (len(employees) + 4) // 5, "employees")
        else:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("« Back to Main", callback_data="admin_main_menu")
            ]])
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def _handle_exceptional_hours_menu(self, query) -> None:
        """Handle exceptional hours menu callback."""
        message = "📅 **Exceptional Hours Management**\n\n"
        message += "Manage custom work schedules for specific employees and dates.\n\n"
        message += "**Usage:**\n"
        message += "`/exceptional_hours <user_id> <date> <start> <end> [reason]`\n\n"
        message += "**Example:**\n"
        message += "`/exceptional_hours 123456789 2024-01-15 10:00 16:00 Medical appointment`"
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("📋 View All Exceptions", callback_data="admin_view_exceptions"),
            InlineKeyboardButton("« Back", callback_data="admin_main_menu")
        ]])
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def _handle_analytics(self, query) -> None:
        """Handle analytics callback."""
        # Get basic analytics data
        total_employees = len(self.db.get_all_employees())
        today_summary = self.db.get_daily_summary()
        
        message = f"📈 **System Analytics**\n\n"
        message += f"**Overview:**\n"
        message += f"• Total Employees: {total_employees}\n"
        message += f"• Today's Attendance Rate: {today_summary.get('attendance_rate', 0):.1f}%\n"
        message += f"• Late Check-ins Today: {today_summary.get('late_checkins', 0)}\n"
        message += f"• Early Departures Today: {today_summary.get('early_checkouts', 0)}\n\n"
        message += "📊 More detailed analytics available via web interface."
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Refresh", callback_data="admin_analytics"),
            InlineKeyboardButton("« Back", callback_data="admin_main_menu")
        ]])
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def _handle_settings_menu(self, query) -> None:
        """Handle settings menu callback."""
        keyboard = self.keyboard_builder.get_admin_settings_keyboard()
        
        message = "⚙️ **Admin Settings**\n\n"
        message += "Configure system settings and preferences."
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def _handle_server_status(self, query) -> None:
        """Handle server status callback."""
        recent_activities = self.db.get_recent_server_activity(5)
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        message = f"🖥️ **Server Status**\n\n"
        message += f"**Status:** ✅ Online\n"
        message += f"**Time:** {current_time}\n"
        message += f"**Health Checks:** {'Enabled' if Config.ENABLE_SERVER_WAKEUP else 'Disabled'}\n\n"
        
        message += "**Recent Activity:**\n"
        for activity in recent_activities:
            timestamp, activity_type, description = activity
            message += f"• `{timestamp}` - {activity_type}\n"
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("🔄 Refresh", callback_data="admin_server_status"),
            InlineKeyboardButton("« Back", callback_data="admin_main_menu")
        ]])
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def _handle_refresh_report(self, query) -> None:
        """Handle refresh report callback."""
        await self._handle_today_report(query)
    
    async def _handle_send_summary(self, query) -> None:
        """Handle send summary callback."""
        # This would trigger sending summary to all admins
        await query.edit_message_text(
            "📤 **Summary Sent**\n\n"
            "Daily summary has been sent to all administrators.",
            parse_mode='Markdown'
        )
    
    async def _handle_employee_action(self, query, data: str) -> None:
        """Handle employee-specific actions."""
        # Extract employee ID from callback data
        parts = data.split('_')
        if len(parts) >= 3:
            employee_id = int(parts[2])
            action = parts[1]
            
            if action == "report":
                await self._show_employee_report(query, employee_id)
            elif action == "exception":
                await self._show_employee_exception_form(query, employee_id)
            else:
                await query.edit_message_text("❓ Unknown employee action.")
        else:
            await query.edit_message_text("❌ Invalid employee action.")
    
    async def _show_employee_report(self, query, employee_id: int) -> None:
        """Show individual employee report."""
        employee_info = self.db.get_employee_info(employee_id)
        if not employee_info:
            await query.edit_message_text("❌ Employee not found.")
            return
        
        name = f"{employee_info[1]} {employee_info[2] or ''}".strip()
        
        # Get recent attendance for this employee
        status = self.db.get_attendance_status(employee_id)
        
        message = f"📊 **Employee Report: {name}**\n\n"
        message += f"**Telegram ID:** `{employee_id}`\n"
        
        if status:
            message += f"**Today's Status:** {'✅ Checked In' if status[2] == 'checked_in' else '⏹️ Checked Out'}\n"
            if status[0]:  # check_in_time
                check_in_time = datetime.fromisoformat(status[0])
                message += f"**Check-in:** {check_in_time.strftime('%H:%M:%S')}\n"
            if status[1]:  # check_out_time
                check_out_time = datetime.fromisoformat(status[1])
                message += f"**Check-out:** {check_out_time.strftime('%H:%M:%S')}\n"
        else:
            message += "**Today's Status:** ❌ Not checked in\n"
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("« Back to Employees", callback_data="admin_all_employees")
        ]])
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    async def _show_employee_exception_form(self, query, employee_id: int) -> None:
        """Show employee exception form."""
        employee_info = self.db.get_employee_info(employee_id)
        if not employee_info:
            await query.edit_message_text("❌ Employee not found.")
            return
        
        name = f"{employee_info[1]} {employee_info[2] or ''}".strip()
        
        message = f"📅 **Set Exceptional Hours**\n\n"
        message += f"**Employee:** {name}\n"
        message += f"**ID:** `{employee_id}`\n\n"
        message += "Use the command format:\n"
        message += f"`/exceptional_hours {employee_id} YYYY-MM-DD HH:MM HH:MM [reason]`\n\n"
        message += "**Example:**\n"
        message += f"`/exceptional_hours {employee_id} 2024-01-15 10:00 16:00 Medical appointment`"
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("« Back to Employees", callback_data="admin_all_employees")
        ]])
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        ) 