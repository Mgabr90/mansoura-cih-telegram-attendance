import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
import pytz

from database import AttendanceDatabase

class CallbackService:
    def __init__(self, db: AttendanceDatabase):
        self.db = db
        self.egypt_tz = pytz.timezone('Africa/Cairo')
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        user = update.effective_user
        
        # Admin panel callbacks
        if query.data == "admin_export_menu":
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
            
        # Export callbacks
        elif query.data == "export_daily_today":
            if self.db.is_admin(user.id):
                await self._export_daily_today(query)
        
        elif query.data == "export_monthly_current":
            if self.db.is_admin(user.id):
                await self._export_monthly_current(query)
        
        elif query.data == "export_employees_list":
            if self.db.is_admin(user.id):
                await self._export_employees(query)
        
        elif query.data == "export_attendance_30days":
            if self.db.is_admin(user.id):
                await self._export_attendance_30days(query)
            
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
            self.db.update_reminder_settings(user.id, reminder_enabled=False, checkout_reminder_enabled=False)
            await query.edit_message_text(
                "🔇 **Reminders Disabled**\n\n"
                "You will no longer receive attendance reminders.\n"
                "You can re-enable them anytime using /reminders command.",
                parse_mode='Markdown'
            )
            
        elif query.data == "view_reminder_settings":
            await self._show_reminder_settings(query, user.id)
            
        # Admin alert callbacks
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
    
    async def _export_daily_today(self, query):
        """Export today's attendance"""
        import io
        
        today = datetime.now(self.egypt_tz).date()
        data = self.db.get_daily_summary_csv(today)
        headers = ['Full Name', 'Username', 'Check In', 'Check Out', 'Work Hours', 'Status']
        
        csv_content = self.db.create_csv_string(data, headers)
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = f"daily_attendance_{today}.csv"
        
        await query.message.reply_document(
            document=csv_file,
            caption=f"📊 Daily Attendance Report - {today}\n📁 {len(data)} employees"
        )
    
    async def _export_monthly_current(self, query):
        """Export current month's attendance"""
        import io
        
        now = datetime.now(self.egypt_tz)
        data = self.db.get_monthly_report_csv(now.year, now.month)
        headers = ['Full Name', 'Username', 'Days Present', 'Avg Work Hours', 'Total Work Hours']
        
        csv_content = self.db.create_csv_string(data, headers)
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = f"monthly_attendance_{now.year}_{now.month:02d}.csv"
        
        await query.message.reply_document(
            document=csv_file,
            caption=f"📊 Monthly Attendance Report - {now.year}/{now.month:02d}\n📁 {len(data)} employees"
        )
    
    async def _export_employees(self, query):
        """Export employee list"""
        import io
        
        data = self.db.get_employee_list_csv()
        headers = ['Telegram ID', 'Full Name', 'Username', 'Phone Number', 'Registration Date', 'Status']
        
        csv_content = self.db.create_csv_string(data, headers)
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = f"employee_list_{datetime.now().strftime('%Y%m%d')}.csv"
        
        await query.message.reply_document(
            document=csv_file,
            caption=f"👥 Employee List Export\n📁 {len(data)} employees"
        )
    
    async def _export_attendance_30days(self, query):
        """Export last 30 days attendance"""
        import io
        from datetime import timedelta
        
        end_date = datetime.now(self.egypt_tz).date()
        start_date = end_date - timedelta(days=30)
        
        data = self.db.export_attendance_csv(start_date, end_date)
        headers = [
            'Full Name', 'Username', 'Phone Number', 'Date', 
            'Check In Time', 'Check Out Time', 'Work Hours', 'Status',
            'Check In Latitude', 'Check In Longitude', 
            'Check Out Latitude', 'Check Out Longitude'
        ]
        
        csv_content = self.db.create_csv_string(data, headers)
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = f"attendance_data_{start_date}_to_{end_date}.csv"
        
        await query.message.reply_document(
            document=csv_file,
            caption=f"📊 Detailed Attendance Export\n📅 {start_date} to {end_date}\n📁 {len(data)} records"
        )
    
    async def _show_reminder_settings(self, query, user_id):
        """Show current reminder settings"""
        with sqlite3.connect(self.db.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT reminder_enabled, reminder_time, checkout_reminder_enabled, checkout_reminder_time
                FROM employees WHERE telegram_id = ?
            ''', (user_id,))
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