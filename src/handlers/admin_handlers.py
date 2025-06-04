import io
from datetime import datetime, timedelta
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

import sys
import os
# Add parent directory to sys.path to import config.py directly
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database_enhanced import EnhancedAttendanceDatabase

# Import config from renamed file to avoid directory conflict
from bot_config import Config

class AdminHandlers:
    """Handler class for admin-related commands and interactions"""
    
    def __init__(self, db: EnhancedAttendanceDatabase):
        self.db = db
        self.config = Config
        self.egypt_tz = pytz.timezone(Config.TIMEZONE)
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin command"""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        keyboard = [
            [InlineKeyboardButton("📊 Today's Report", callback_data="admin_today_report")],
            [InlineKeyboardButton("📈 All Employees Report", callback_data="admin_all_report")],
            [InlineKeyboardButton("📁 Export Data", callback_data="admin_export_menu")],
            [InlineKeyboardButton("👥 Employee List", callback_data="admin_employee_list")],
            [InlineKeyboardButton("🚨 Alert Settings", callback_data="admin_alert_settings")]
        ]
        
        await update.message.reply_text(
            "🔧 **Admin Panel**\n\nSelect an option:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def add_admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /add_admin command"""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        if not context.args:
            await update.message.reply_text(
                "📝 **Add Admin**\n\n"
                "Usage: `/add_admin <user_id>`\n"
                "Example: `/add_admin 123456789`\n\n"
                "💡 You can get user ID from forwarded messages or by asking the user to send /myid",
                parse_mode='Markdown'
            )
            return
        
        try:
            new_admin_id = int(context.args[0])
            self.db.add_admin(new_admin_id)
            
            await update.message.reply_text(
                f"✅ **Admin Added Successfully**\n\n"
                f"User ID {new_admin_id} has been granted admin privileges.\n"
                f"They can now:\n"
                f"• Add exceptional working hours\n"
                f"• Receive daily summaries\n"
                f"• Manage other admins\n"
                f"• View all attendance reports",
                parse_mode='Markdown'
            )
            
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID. Please provide a numeric user ID.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error adding admin: {str(e)}")
    
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
            "🚨 **Alert Settings**\n\n"
            f"Admin alerts are currently {'enabled' if alert_enabled else 'disabled'}.\n"
            f"Late threshold: {late_threshold} minutes",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 Toggle Alerts", callback_data="toggle_admin_alerts")],
                [InlineKeyboardButton("⏱️ Set Late Threshold", callback_data="set_late_threshold")],
                [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_admin_alerts")]
            ]),
            parse_mode='Markdown'
        )
    
    async def handle_admin_callbacks(self, query, user):
        """Handle admin-specific callback queries"""
        if query.data == "admin_today_report":
            # Trigger all report command
            return "all_report"
            
        elif query.data == "admin_export_menu":
            await query.edit_message_text(
                "📁 **Export Data**\n\nSelect an option:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📊 Weekly Report", callback_data="weekly_report")],
                    [InlineKeyboardButton("📋 Detailed Logs", callback_data="view_logs")]
                ]),
                parse_mode='Markdown'
            )
            
        elif query.data == "admin_alert_settings":
            alert_enabled, late_threshold = self.db.get_admin_alert_settings(user.id)
            await query.edit_message_text(
                "🚨 **Alert Settings**\n\n"
                f"Admin alerts are currently {'enabled' if alert_enabled else 'disabled'}.\n"
                f"Late threshold: {late_threshold} minutes",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Toggle Alerts", callback_data="toggle_admin_alerts")],
                    [InlineKeyboardButton("⏱️ Set Late Threshold", callback_data="set_late_threshold")],
                    [InlineKeyboardButton("🔄 Refresh", callback_data="refresh_admin_alerts")]
                ]),
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
                "Enter the new late threshold in minutes:",
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

    async def exceptional_hours_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /exceptional_hours command"""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        if len(context.args) < 4:
            await update.message.reply_text(
                "📅 **Add Exceptional Working Hours**\n\n"
                "Usage: `/exceptional_hours <user_id> <date> <start_time> <end_time> [reason]`\n\n"
                "Examples:\n"
                "• `/exceptional_hours 123456789 2024-01-15 08:00 16:00 Early shift`\n"
                "• `/exceptional_hours 123456789 2024-01-15 10:00 18:00 Doctor appointment`\n\n"
                "📝 Format:\n"
                "• Date: YYYY-MM-DD\n"
                "• Time: HH:MM (24-hour format)\n"
                "• Reason: Optional description",
                parse_mode='Markdown'
            )
            return
        
        try:
            employee_id = int(context.args[0])
            date_str = context.args[1]
            start_time = context.args[2]
            end_time = context.args[3]
            reason = " ".join(context.args[4:]) if len(context.args) > 4 else "Admin adjusted hours"
            
            # Validate date format
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            
            # Validate time format
            datetime.strptime(start_time, '%H:%M')
            datetime.strptime(end_time, '%H:%M')
            
            # Check if employee exists
            if not self.db.is_employee_registered(employee_id):
                await update.message.reply_text(f"❌ Employee with ID {employee_id} is not registered.")
                return
            
            # Add exceptional hours
            self.db.add_exceptional_hours(
                telegram_id=employee_id,
                date=date_obj,
                work_start=start_time,
                work_end=end_time,
                reason=reason,
                created_by=user.id
            )
            
            await update.message.reply_text(
                f"✅ **Exceptional Hours Added**\n\n"
                f"👤 Employee ID: {employee_id}\n"
                f"📅 Date: {date_str}\n"
                f"⏰ Work Hours: {start_time} - {end_time}\n"
                f"📝 Reason: {reason}\n\n"
                f"The employee will work these hours instead of their standard schedule for this date.",
                parse_mode='Markdown'
            )
            
        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid format: {str(e)}")
        except Exception as e:
            await update.message.reply_text(f"❌ Error adding exceptional hours: {str(e)}")
    
    async def admin_report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /admin_report command"""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        # Get current day summary
        egypt_tz = pytz.timezone(self.config.TIMEZONE)
        current_date = datetime.now(egypt_tz).date()
        
        summary = self.db.get_daily_summary_for_admins(current_date)
        
        # Build report message
        message = f"""
📊 **Admin Dashboard - {current_date}**

👥 **Employee Overview:**
• Total Employees: {summary['total_employees']}
• Checked In Today: {summary['checked_in']}
• Checked Out Today: {summary['checked_out']}
• Currently Working: {summary['checked_in'] - summary['checked_out']}

⏰ **Attendance Issues:**
• Late Check-ins: {summary['late_checkins']}
• Early Check-outs: {summary['early_checkouts']}
"""
        
        # Calculate attendance rate
        attendance_rate = (summary['checked_in'] / summary['total_employees']) * 100 if summary['total_employees'] > 0 else 0
        message += f"\n📈 **Attendance Rate: {attendance_rate:.1f}%**"
        
        # Add late employees
        if summary['late_employees']:
            message += "\n\n🕐 **Late Arrivals:**"
            for emp in summary['late_employees']:
                name = f"{emp[0]} {emp[1] or ''}".strip()
                check_in_time = datetime.fromisoformat(emp[2]).strftime('%H:%M')
                reason = emp[3] if emp[3] else "No reason"
                message += f"\n• {name} - {check_in_time} ({reason})"
        
        # Add early checkouts
        if summary['early_employees']:
            message += "\n\n🕕 **Early Departures:**"
            for emp in summary['early_employees']:
                name = f"{emp[0]} {emp[1] or ''}".strip()
                check_out_time = datetime.fromisoformat(emp[2]).strftime('%H:%M')
                reason = emp[3] if emp[3] else "No reason"
                message += f"\n• {name} - {check_out_time} ({reason})"
        
        # Add quick action buttons
        keyboard = [
            [
                InlineKeyboardButton("📅 Add Exceptional Hours", callback_data="add_exceptional"),
                InlineKeyboardButton("👥 View All Employees", callback_data="view_employees")
            ],
            [
                InlineKeyboardButton("📊 Weekly Report", callback_data="weekly_report"),
                InlineKeyboardButton("🔄 Refresh", callback_data="refresh_report")
            ]
        ]
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def list_employees_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /list_employees command"""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        try:
            with self.db.db_name as db_path:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT telegram_id, first_name, last_name, username, phone_number, 
                           standard_work_start, standard_work_end, is_active
                    FROM employees
                    ORDER BY first_name
                ''')
                
                employees = cursor.fetchall()
                conn.close()
            
            if not employees:
                await update.message.reply_text("👥 No employees found in the system.")
                return
            
            message = "👥 **Employee Directory**\n\n"
            
            for emp in employees:
                telegram_id, first_name, last_name, username, phone, work_start, work_end, is_active = emp
                name = f"{first_name} {last_name or ''}".strip()
                username_str = f"@{username}" if username else "No username"
                status = "✅ Active" if is_active else "❌ Inactive"
                
                message += f"""
**{name}** ({status})
• ID: {telegram_id}
• Username: {username_str}
• Phone: {phone or 'Not provided'}
• Work Hours: {work_start} - {work_end}
---
"""
            
            # Split message if too long
            if len(message) > 4000:
                parts = message.split('---')
                current_part = "👥 **Employee Directory**\n\n"
                
                for part in parts[:-1]:  # Exclude last empty part
                    if len(current_part + part + '---\n') > 4000:
                        await update.message.reply_text(current_part, parse_mode='Markdown')
                        current_part = part + '---\n'
                    else:
                        current_part += part + '---\n'
                
                if current_part.strip():
                    await update.message.reply_text(current_part, parse_mode='Markdown')
            else:
                await update.message.reply_text(message, parse_mode='Markdown')
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error retrieving employee list: {str(e)}")
    
    async def server_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /server_status command"""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        try:
            with self.db.db_name as db_path:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get recent server activity
                cursor.execute('''
                    SELECT activity_type, timestamp, details
                    FROM server_activity
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''')
                
                activities = cursor.fetchall()
                
                # Get notification stats
                cursor.execute('''
                    SELECT notification_type, COUNT(*) as count
                    FROM notification_log
                    WHERE date(sent_at) = date('now')
                    GROUP BY notification_type
                ''')
                
                notifications = cursor.fetchall()
                conn.close()
            
            egypt_tz = pytz.timezone(self.config.TIMEZONE)
            current_time = datetime.now(egypt_tz)
            
            message = f"""
🖥️ **Server Status Report**

⏰ Current Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}
🌐 Location: El Mansoura, Egypt
📡 Status: Online

📊 **Today's Notifications:**
"""
            
            if notifications:
                for notif_type, count in notifications:
                    message += f"• {notif_type}: {count}\n"
            else:
                message += "• No notifications sent today\n"
            
            message += "\n🔄 **Recent Activity:**\n"
            
            if activities:
                for activity in activities[:5]:  # Show last 5 activities
                    activity_type, timestamp, details = activity
                    time_str = datetime.fromisoformat(timestamp).strftime('%H:%M:%S')
                    message += f"• {time_str} - {activity_type}"
                    if details:
                        message += f" ({details})"
                    message += "\n"
            else:
                message += "• No recent activity logged\n"
            
            keyboard = [
                [InlineKeyboardButton("🔄 Refresh Status", callback_data="refresh_status")],
                [InlineKeyboardButton("📊 View Logs", callback_data="view_logs")]
            ]
            
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error retrieving server status: {str(e)}")
    
    async def handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        user = query.from_user
        
        if not self.db.is_admin(user.id):
            await query.answer("❌ Admin privileges required")
            return
        
        await query.answer()
        
        if query.data == "refresh_report":
            # Refresh admin report
            await self.admin_report_command(update, context)
        
        elif query.data == "add_exceptional":
            await query.edit_message_text(
                "📅 **Add Exceptional Working Hours**\n\n"
                "Use command: `/exceptional_hours <user_id> <date> <start_time> <end_time> [reason]`\n\n"
                "Example: `/exceptional_hours 123456789 2024-01-15 08:00 16:00 Early shift`",
                parse_mode='Markdown'
            )
        
        elif query.data == "view_employees":
            await self.list_employees_command(update, context)
        
        elif query.data == "weekly_report":
            await self._send_weekly_report(update)
        
        elif query.data == "refresh_status":
            await self.server_status_command(update, context)
        
        elif query.data == "view_logs":
            await self._send_detailed_logs(update)
    
    async def _send_weekly_report(self, update):
        """Send weekly attendance report"""
        try:
            egypt_tz = pytz.timezone(self.config.TIMEZONE)
            end_date = datetime.now(egypt_tz).date()
            start_date = end_date - timedelta(days=7)
            
            with self.db.db_name as db_path:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get weekly stats
                cursor.execute('''
                    SELECT date, COUNT(*) as check_ins,
                           SUM(CASE WHEN is_late = 1 THEN 1 ELSE 0 END) as late_count,
                           SUM(CASE WHEN is_early_checkout = 1 THEN 1 ELSE 0 END) as early_count
                    FROM attendance
                    WHERE date BETWEEN ? AND ?
                    GROUP BY date
                    ORDER BY date DESC
                ''', (start_date, end_date))
                
                daily_stats = cursor.fetchall()
                conn.close()
            
            message = f"""
📊 **Weekly Report ({start_date} to {end_date})**

📈 **Daily Breakdown:**
"""
            
            total_checkins = 0
            total_late = 0
            total_early = 0
            
            for stat in daily_stats:
                date, checkins, late, early = stat
                total_checkins += checkins
                total_late += late
                total_early += early
                
                message += f"\n📅 {date}: {checkins} check-ins"
                if late > 0:
                    message += f" ({late} late)"
                if early > 0:
                    message += f" ({early} early)"
            
            if daily_stats:
                avg_checkins = total_checkins / len(daily_stats)
                message += f"""

📊 **Weekly Summary:**
• Total Check-ins: {total_checkins}
• Average per day: {avg_checkins:.1f}
• Late arrivals: {total_late}
• Early departures: {total_early}
"""
            else:
                message += "\n❌ No attendance data for this week"
            
            await update.effective_message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            await update.effective_message.reply_text(f"❌ Error generating weekly report: {str(e)}")
    
    async def _send_detailed_logs(self, update):
        """Send detailed server logs"""
        try:
            with self.db.db_name as db_path:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT activity_type, timestamp, details
                    FROM server_activity
                    ORDER BY timestamp DESC
                    LIMIT 20
                ''')
                
                logs = cursor.fetchall()
                conn.close()
            
            message = "📋 **Detailed Server Logs (Last 20 entries)**\n\n"
            
            if logs:
                for log in logs:
                    activity_type, timestamp, details = log
                    time_str = datetime.fromisoformat(timestamp).strftime('%m-%d %H:%M:%S')
                    message += f"`{time_str}` {activity_type}"
                    if details:
                        message += f" - {details}"
                    message += "\n"
            else:
                message += "❌ No logs found"
            
            await update.effective_message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            await update.effective_message.reply_text(f"❌ Error retrieving logs: {str(e)}") 