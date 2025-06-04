import io
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import AttendanceDatabase
from utils.keyboards import Keyboards
from utils.messages import Messages
from config.settings import TIMEZONE

class AdminHandlers:
    """Handler class for admin-related commands and interactions"""
    
    def __init__(self, db: AttendanceDatabase):
        self.db = db
        self.egypt_tz = pytz.timezone(TIMEZONE)
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        await update.message.reply_text(
            Messages.admin_panel(),
            reply_markup=Keyboards.get_admin_panel_keyboard(),
            parse_mode='Markdown'
        )
    
    async def add_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add_admin command"""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Please provide a user ID: /add_admin <user_id>")
            return
        
        try:
            new_admin_id = int(context.args[0])
            self.db.add_admin(new_admin_id)
            await update.message.reply_text(f"✅ User {new_admin_id} has been added as admin.")
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")
    
    async def all_report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /all_report command"""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        report_data = self.db.get_all_employees_report()
        today = datetime.now(self.egypt_tz).date().strftime('%Y-%m-%d')
        
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
    
    async def admin_alerts_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin alert settings"""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        alert_enabled, late_threshold = self.db.get_admin_alert_settings(user.id)
        
        await update.message.reply_text(
            Messages.admin_alerts_info(alert_enabled, late_threshold),
            reply_markup=Keyboards.get_admin_alerts_keyboard(alert_enabled),
            parse_mode='Markdown'
        )
    
    async def handle_admin_callbacks(self, query, user):
        """Handle admin-specific callback queries"""
        if query.data == "admin_today_report":
            # Trigger all report command
            return "all_report"
            
        elif query.data == "admin_export_menu":
            await query.edit_message_text(
                Messages.export_menu(),
                reply_markup=Keyboards.get_export_menu_keyboard(),
                parse_mode='Markdown'
            )
            
        elif query.data == "admin_alert_settings":
            alert_enabled, late_threshold = self.db.get_admin_alert_settings(user.id)
            await query.edit_message_text(
                Messages.admin_alerts_info(alert_enabled, late_threshold),
                reply_markup=Keyboards.get_admin_alerts_keyboard(alert_enabled),
                parse_mode='Markdown'
            )
            
        elif query.data == "toggle_admin_alerts":
            if self.db.is_admin(user.id):
                current_setting, threshold = self.db.get_admin_alert_settings(user.id)
                new_setting = not current_setting
                self.db.update_admin_alert_settings(user.id, alert_enabled=new_setting)
                
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
            if self.db.is_admin(user.id):
                test_message = """
🧪 **Test Alert**

This is a test admin alert to verify your notification settings are working correctly.

✅ If you received this message, alerts are configured properly.
                """
                await query.message.reply_text(test_message, parse_mode='Markdown')
        
        return None 