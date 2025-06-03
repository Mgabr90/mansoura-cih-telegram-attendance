import asyncio
import logging
from datetime import datetime, time
import pytz
from telegram import Bot
from database import AttendanceDatabase

class NotificationService:
    def __init__(self, bot_token, db: AttendanceDatabase):
        self.bot = Bot(token=bot_token)
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.egypt_tz = pytz.timezone('Africa/Cairo')
        
    async def send_checkin_reminders(self):
        """Send check-in reminders to employees"""
        current_time = datetime.now(self.egypt_tz).time()
        employees = self.db.get_employees_for_checkin_reminder(current_time)
        
        for employee in employees:
            telegram_id, first_name, reminder_time = employee
            
            message = f"""
🔔 **Check-in Reminder**

Good morning {first_name}! 

⏰ It's {reminder_time} - time to check in to the office.
📍 Remember to be within 100m of El Mansoura office location.

Tap the button below to check in:
            """
            
            try:
                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=message,
                    parse_mode='Markdown'
                )
                
                self.db.log_notification(telegram_id, 'checkin_reminder', message)
                self.logger.info(f"Check-in reminder sent to {first_name} ({telegram_id})")
                
            except Exception as e:
                self.logger.error(f"Failed to send check-in reminder to {telegram_id}: {e}")

    async def send_checkout_reminders(self):
        """Send check-out reminders to employees"""
        current_time = datetime.now(self.egypt_tz).time()
        employees = self.db.get_employees_for_checkout_reminder(current_time)
        
        for employee in employees:
            telegram_id, first_name, checkout_time = employee
            
            message = f"""
🔔 **Check-out Reminder**

Hi {first_name}! 

⏰ It's {checkout_time} - don't forget to check out.
📊 Make sure to record your departure time.

Tap the button below to check out:
            """
            
            try:
                await self.bot.send_message(
                    chat_id=telegram_id,
                    text=message,
                    parse_mode='Markdown'
                )
                
                self.db.log_notification(telegram_id, 'checkout_reminder', message)
                self.logger.info(f"Check-out reminder sent to {first_name} ({telegram_id})")
                
            except Exception as e:
                self.logger.error(f"Failed to send check-out reminder to {telegram_id}: {e}")

    async def send_late_alerts_to_admins(self):
        """Send late check-in alerts to administrators"""
        admins = self.db.get_all_admins_for_alerts()
        
        for admin_id, late_threshold in admins:
            late_employees = self.db.get_late_employees(late_threshold)
            
            if late_employees:
                message = f"""
🚨 **Late Check-in Alert**

{len(late_employees)} employee(s) are late for check-in:

"""
                for employee in late_employees:
                    telegram_id, first_name, last_name, username, expected_time = employee
                    full_name = f"{first_name} {last_name or ''}".strip()
                    username_str = f"@{username}" if username else "No username"
                    
                    current_time = datetime.now(self.egypt_tz).time()
                    late_minutes = self._calculate_late_minutes(expected_time, current_time.strftime('%H:%M'))
                    
                    message += f"• **{full_name}** ({username_str}) - {late_minutes} minutes late\n"
                
                message += f"\n⏰ Threshold: {late_threshold} minutes\n📅 Date: {datetime.now(self.egypt_tz).strftime('%Y-%m-%d')}"
                
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    
                    self.db.log_notification(admin_id, 'late_alert', message)
                    self.logger.info(f"Late alert sent to admin {admin_id}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to send late alert to admin {admin_id}: {e}")

    async def send_missed_checkout_alerts(self):
        """Send missed check-out alerts to administrators"""
        admins = self.db.get_all_admins_for_alerts()
        missed_employees = self.db.get_missed_checkout_employees(10)  # 10+ hours
        
        if missed_employees:
            message = f"""
⚠️ **Missed Check-out Alert**

{len(missed_employees)} employee(s) forgot to check out:

"""
            for employee in missed_employees:
                telegram_id, first_name, last_name, username, checkin_time = employee
                full_name = f"{first_name} {last_name or ''}".strip()
                username_str = f"@{username}" if username else "No username"
                
                checkin_dt = datetime.fromisoformat(checkin_time)
                hours_worked = (datetime.now(self.egypt_tz) - checkin_dt).total_seconds() / 3600
                
                message += f"• **{full_name}** ({username_str}) - {hours_worked:.1f} hours since check-in\n"
            
            message += f"\n📅 Date: {datetime.now(self.egypt_tz).strftime('%Y-%m-%d')}"
            
            for admin_id, _ in admins:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    
                    self.db.log_notification(admin_id, 'missed_checkout_alert', message)
                    self.logger.info(f"Missed checkout alert sent to admin {admin_id}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to send missed checkout alert to admin {admin_id}: {e}")

    def _calculate_late_minutes(self, expected_time_str, current_time_str):
        """Calculate how many minutes late an employee is"""
        try:
            expected = datetime.strptime(expected_time_str, '%H:%M').time()
            current = datetime.strptime(current_time_str, '%H:%M').time()
            
            expected_minutes = expected.hour * 60 + expected.minute
            current_minutes = current.hour * 60 + current.minute
            
            return max(0, current_minutes - expected_minutes)
        except:
            return 0

    async def run_scheduler(self):
        """Run the notification scheduler"""
        while True:
            try:
                current_time = datetime.now(self.egypt_tz).time()
                
                # Send reminders every minute during work hours
                if time(6, 0) <= current_time <= time(20, 0):
                    await self.send_checkin_reminders()
                    await self.send_checkout_reminders()
                
                # Send late alerts every 30 minutes during morning hours
                if current_time.minute in [0, 30] and time(9, 0) <= current_time <= time(12, 0):
                    await self.send_late_alerts_to_admins()
                
                # Send missed checkout alerts at end of day
                if current_time == time(20, 0):
                    await self.send_missed_checkout_alerts()
                
                # Wait 1 minute before next check
                await asyncio.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Error in notification scheduler: {e}")
                await asyncio.sleep(60)  # Continue after error 