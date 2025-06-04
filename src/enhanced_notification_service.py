import asyncio
import logging
import aiohttp
import os
import sys
from datetime import datetime, time
import pytz
from telegram import Bot

# Fix import path
sys.path.append(os.path.dirname(__file__))
from database_enhanced import EnhancedAttendanceDatabase

class EnhancedNotificationService:
    def __init__(self, bot_token, db: EnhancedAttendanceDatabase):
        self.bot = Bot(token=bot_token)
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.egypt_tz = pytz.timezone('Africa/Cairo')
        
        # Server wake-up configuration
        self.server_url = os.getenv('SERVER_URL', '')  # Set this in production
        self.wake_up_interval = 14 * 60  # 14 minutes (Render free tier sleeps after 15 minutes)
        
    async def send_daily_summary_to_admins(self):
        """Send daily attendance summary to all admins at 8 PM"""
        try:
            current_time = datetime.now(self.egypt_tz)
            summary = self.db.get_daily_summary_for_admins(current_time.date())
            admins = self.db.get_all_admins_for_daily_summary()
            
            if not admins:
                self.logger.info("No admins configured to receive daily summary")
                return
            
            # Build comprehensive summary message
            message = f"""
📊 **Daily Attendance Summary - {summary['date']}**

👥 **Overview:**
• Total Employees: {summary['total_employees']}
• Checked In Today: {summary['checked_in']}
• Checked Out Today: {summary['checked_out']}
• Still Working: {summary['checked_in'] - summary['checked_out']}

⏰ **Attendance Issues:**
• Late Check-ins: {summary['late_checkins']}
• Early Check-outs: {summary['early_checkouts']}
"""

            # Add late employees details
            if summary['late_employees']:
                message += "\n🕐 **Late Arrivals:**\n"
                for emp in summary['late_employees']:
                    name = f"{emp[0]} {emp[1] or ''}".strip()
                    check_in_time = datetime.fromisoformat(emp[2]).strftime('%H:%M')
                    reason = emp[3] if emp[3] else "No reason provided"
                    message += f"• {name} - {check_in_time} ({reason})\n"
            
            # Add early checkout details
            if summary['early_employees']:
                message += "\n🕕 **Early Departures:**\n"
                for emp in summary['early_employees']:
                    name = f"{emp[0]} {emp[1] or ''}".strip()
                    check_out_time = datetime.fromisoformat(emp[2]).strftime('%H:%M')
                    reason = emp[3] if emp[3] else "No reason provided"
                    message += f"• {name} - {check_out_time} ({reason})\n"
            
            # Calculate attendance rate
            attendance_rate = (summary['checked_in'] / summary['total_employees']) * 100 if summary['total_employees'] > 0 else 0
            message += f"\n📈 **Daily Attendance Rate: {attendance_rate:.1f}%**"
            
            # Add timestamp
            message += f"\n\n🕘 Report generated at {current_time.strftime('%H:%M:%S')}"
            
            # Send to all admins
            for admin_id in admins:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    
                    self.db.log_notification(admin_id, 'daily_summary', message)
                    self.logger.info(f"Daily summary sent to admin {admin_id}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to send daily summary to admin {admin_id}: {e}")
            
            # Log server activity
            self.db.log_server_activity('daily_summary_sent', 
                                       f"Sent to {len(admins)} admins. Rate: {attendance_rate:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Error in daily summary service: {e}")
    
    async def wake_up_server(self):
        """Wake up server by making HTTP request to prevent sleep"""
        if not self.server_url:
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.server_url}/health", 
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        self.logger.info("Server wake-up ping successful")
                        self.db.log_server_activity('wake_up_ping', 'Success')
                    else:
                        self.logger.warning(f"Server wake-up ping returned status {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Failed to wake up server: {e}")
            self.db.log_server_activity('wake_up_ping', f'Failed: {str(e)}')
    
    async def send_enhanced_late_alerts(self):
        """Send enhanced late check-in alerts with reasons to administrators"""
        try:
            current_time = datetime.now(self.egypt_tz)
            
            # Get all admins
            admins = self.db.get_all_admins_for_daily_summary()
            
            if not admins:
                return
            
            # Get late employees with their reasons
            with self.db.db_name as db_path:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT e.telegram_id, e.first_name, e.last_name, e.username, 
                           a.check_in_time, a.late_reason, e.standard_work_start
                    FROM attendance a
                    JOIN employees e ON a.telegram_id = e.telegram_id
                    WHERE a.date = ? AND a.is_late = 1
                ''', (current_time.date(),))
                
                late_employees = cursor.fetchall()
                conn.close()
            
            if not late_employees:
                return
            
            message = f"""
🚨 **Enhanced Late Check-in Alert**

📅 Date: {current_time.strftime('%Y-%m-%d')}
⏰ Alert Time: {current_time.strftime('%H:%M:%S')}

{len(late_employees)} employee(s) are late today:

"""
            
            for emp in late_employees:
                name = f"{emp[1]} {emp[2] or ''}".strip()
                username = f"@{emp[3]}" if emp[3] else "No username"
                check_in_time = datetime.fromisoformat(emp[4]).strftime('%H:%M')
                work_start = emp[6]
                reason = emp[5] if emp[5] else "❌ No reason provided"
                
                # Calculate lateness
                work_start_time = datetime.strptime(work_start, '%H:%M').time()
                check_in_dt = datetime.fromisoformat(emp[4])
                check_in_time_only = check_in_dt.time()
                
                work_start_minutes = work_start_time.hour * 60 + work_start_time.minute
                check_in_minutes = check_in_time_only.hour * 60 + check_in_time_only.minute
                late_minutes = check_in_minutes - work_start_minutes
                
                message += f"""
👤 **{name}** ({username})
⏰ Expected: {work_start} | Arrived: {check_in_time}
🕒 Late by: {late_minutes} minutes
📝 Reason: {reason}
---
"""
            
            # Send to all admins
            for admin_id in admins:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    
                    self.db.log_notification(admin_id, 'enhanced_late_alert', message)
                    
                except Exception as e:
                    self.logger.error(f"Failed to send enhanced late alert to admin {admin_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in enhanced late alerts: {e}")
    
    async def send_checkin_reminders(self):
        """Send check-in reminders to employees"""
        try:
            current_time = datetime.now(self.egypt_tz).time()
            
            # Get employees who need reminders
            with self.db.db_name as db_path:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get employees with reminder enabled and no check-in today
                cursor.execute('''
                    SELECT e.telegram_id, e.first_name, e.reminder_time, e.standard_work_start
                    FROM employees e
                    LEFT JOIN attendance a ON e.telegram_id = a.telegram_id AND a.date = ?
                    WHERE e.reminder_enabled = 1 
                    AND e.reminder_time = ?
                    AND a.id IS NULL
                    AND e.is_active = 1
                ''', (datetime.now(self.egypt_tz).date(), current_time.strftime('%H:%M')))
                
                employees = cursor.fetchall()
                conn.close()
            
            for employee in employees:
                telegram_id, first_name, reminder_time, work_start = employee
                
                message = f"""
🔔 **Check-in Reminder**

Good morning {first_name}! 

⏰ It's {reminder_time} - time to check in to the office.
🏢 Work starts at {work_start}
📍 Remember to be within 100m of El Mansoura office location.

🚨 **Important:** Location sharing is required - manual entry is disabled.

Tap the 'Check In' button and share your location to record attendance.
"""
                
                try:
                    await self.bot.send_message(
                        chat_id=telegram_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    
                    self.db.log_notification(telegram_id, 'checkin_reminder', message)
                    self.logger.info(f"Enhanced check-in reminder sent to {first_name} ({telegram_id})")
                    
                except Exception as e:
                    self.logger.error(f"Failed to send check-in reminder to {telegram_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in check-in reminders: {e}")
    
    async def send_checkout_reminders(self):
        """Send check-out reminders to employees"""
        try:
            current_time = datetime.now(self.egypt_tz).time()
            
            with self.db.db_name as db_path:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get employees who are checked in and need checkout reminder
                cursor.execute('''
                    SELECT e.telegram_id, e.first_name, e.checkout_reminder_time, e.standard_work_end
                    FROM employees e
                    JOIN attendance a ON e.telegram_id = a.telegram_id
                    WHERE e.checkout_reminder_enabled = 1
                    AND e.checkout_reminder_time = ?
                    AND a.date = ?
                    AND a.check_out_time IS NULL
                    AND e.is_active = 1
                ''', (current_time.strftime('%H:%M'), datetime.now(self.egypt_tz).date()))
                
                employees = cursor.fetchall()
                conn.close()
            
            for employee in employees:
                telegram_id, first_name, reminder_time, work_end = employee
                
                message = f"""
🔔 **Check-out Reminder**

Hi {first_name}! 

⏰ It's {reminder_time} - don't forget to check out.
🏢 Work ends at {work_end}
📊 Make sure to record your departure time.

🚨 **Important:** Location sharing is required for check-out.

Tap the 'Check Out' button and share your location to complete your workday.
"""
                
                try:
                    await self.bot.send_message(
                        chat_id=telegram_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    
                    self.db.log_notification(telegram_id, 'checkout_reminder', message)
                    self.logger.info(f"Enhanced check-out reminder sent to {first_name} ({telegram_id})")
                    
                except Exception as e:
                    self.logger.error(f"Failed to send check-out reminder to {telegram_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in check-out reminders: {e}")
    
    async def send_missed_checkout_alerts(self):
        """Send missed check-out alerts to administrators"""
        try:
            with self.db.db_name as db_path:
                import sqlite3
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get employees who forgot to check out (more than 10 hours)
                cursor.execute('''
                    SELECT e.telegram_id, e.first_name, e.last_name, e.username, a.check_in_time
                    FROM employees e
                    JOIN attendance a ON e.telegram_id = a.telegram_id
                    WHERE a.date = ?
                    AND a.check_out_time IS NULL
                    AND (julianday('now') - julianday(a.check_in_time)) * 24 > 10
                ''', (datetime.now(self.egypt_tz).date(),))
                
                missed_employees = cursor.fetchall()
                conn.close()
            
            if not missed_employees:
                return
            
            admins = self.db.get_all_admins_for_daily_summary()
            
            message = f"""
⚠️ **Missed Check-out Alert**

📅 Date: {datetime.now(self.egypt_tz).strftime('%Y-%m-%d')}

{len(missed_employees)} employee(s) forgot to check out:

"""
            
            for employee in missed_employees:
                telegram_id, first_name, last_name, username, checkin_time = employee
                full_name = f"{first_name} {last_name or ''}".strip()
                username_str = f"@{username}" if username else "No username"
                
                checkin_dt = datetime.fromisoformat(checkin_time)
                hours_worked = (datetime.now(self.egypt_tz) - checkin_dt).total_seconds() / 3600
                
                message += f"• **{full_name}** ({username_str}) - {hours_worked:.1f} hours since check-in\n"
            
            message += f"\n📱 Please remind them to check out using the location-sharing feature."
            
            for admin_id in admins:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    
                    self.db.log_notification(admin_id, 'missed_checkout_alert', message)
                    
                except Exception as e:
                    self.logger.error(f"Failed to send missed checkout alert to admin {admin_id}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in missed checkout alerts: {e}")
    
    async def run_enhanced_scheduler(self):
        """Run the enhanced notification scheduler with server wake-up"""
        self.logger.info("Starting enhanced notification scheduler...")
        
        while True:
            try:
                current_time = datetime.now(self.egypt_tz).time()
                current_minute = current_time.strftime('%H:%M')
                
                # Server wake-up every 14 minutes to prevent sleep
                if current_time.minute % 14 == 0 and current_time.second < 5:
                    await self.wake_up_server()
                
                # Daily summary at 8:00 PM (20:00)
                if current_minute == "20:00":
                    await self.send_daily_summary_to_admins()
                
                # Send reminders every minute during work hours
                if time(6, 0) <= current_time <= time(20, 0):
                    await self.send_checkin_reminders()
                    await self.send_checkout_reminders()
                
                # Enhanced late alerts every 30 minutes during morning hours
                if current_time.minute in [0, 30] and time(9, 0) <= current_time <= time(12, 0):
                    await self.send_enhanced_late_alerts()
                
                # Missed checkout alerts at end of day (8 PM)
                if current_minute == "20:00":
                    await self.send_missed_checkout_alerts()
                
                # Log activity periodically
                if current_time.minute == 0:  # Every hour
                    self.db.log_server_activity('scheduler_heartbeat', f'Active at {current_minute}')
                
                # Wait 60 seconds before next check
                await asyncio.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Error in enhanced notification scheduler: {e}")
                await asyncio.sleep(60)  # Continue after error 