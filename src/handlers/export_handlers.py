import io
from datetime import datetime, timedelta
import pytz
from telegram import Update
from telegram.ext import ContextTypes

from database import AttendanceDatabase

class ExportHandlers:
    def __init__(self, db: AttendanceDatabase):
        self.db = db
        self.egypt_tz = pytz.timezone('Africa/Cairo')
    
    async def export_daily_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Export daily attendance report as CSV"""
        user = update.effective_user
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        # Parse date if provided, otherwise use today
        date = datetime.now(self.egypt_tz).date()
        
        if context.args:
            try:
                date = datetime.strptime(context.args[0], '%Y-%m-%d').date()
            except ValueError:
                await update.message.reply_text("❌ Invalid date format. Use YYYY-MM-DD")
                return
        
        # Get data
        data = self.db.get_daily_summary_csv(date)
        headers = ['Full Name', 'Username', 'Check In', 'Check Out', 'Work Hours', 'Status']
        
        # Create CSV
        csv_content = self.db.create_csv_string(data, headers)
        
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
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        # Parse year and month if provided
        now = datetime.now(self.egypt_tz)
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
        data = self.db.get_monthly_report_csv(year, month)
        headers = ['Full Name', 'Username', 'Days Present', 'Avg Work Hours', 'Total Work Hours']
        
        # Create CSV
        csv_content = self.db.create_csv_string(data, headers)
        
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
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        # Get data
        data = self.db.get_employee_list_csv()
        headers = ['Telegram ID', 'Full Name', 'Username', 'Phone Number', 'Registration Date', 'Status']
        
        # Create CSV
        csv_content = self.db.create_csv_string(data, headers)
        
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
        
        if not self.db.is_admin(user.id):
            await update.message.reply_text("❌ You don't have admin privileges.")
            return
        
        # Parse date range if provided
        end_date = datetime.now(self.egypt_tz).date()
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
        data = self.db.export_attendance_csv(start_date, end_date)
        headers = [
            'Full Name', 'Username', 'Phone Number', 'Date', 
            'Check In Time', 'Check Out Time', 'Work Hours', 'Status',
            'Check In Latitude', 'Check In Longitude', 
            'Check Out Latitude', 'Check Out Longitude'
        ]
        
        # Create CSV
        csv_content = self.db.create_csv_string(data, headers)
        
        # Send as file
        csv_file = io.BytesIO(csv_content.encode('utf-8'))
        csv_file.name = f"attendance_data_{start_date}_to_{end_date}.csv"
        
        await update.message.reply_document(
            document=csv_file,
            caption=f"📊 Detailed Attendance Export\n📅 {start_date} to {end_date}\n📁 {len(data)} records"
        ) 