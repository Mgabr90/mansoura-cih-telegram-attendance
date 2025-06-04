"""
Notification service module for the Enhanced Attendance System.

This module handles scheduled notifications, daily summaries, and alert services.
"""

import asyncio
import logging
from datetime import datetime, time
from typing import Optional

from telegram import Bot

from ..core.database import AttendanceDatabase
from ..core.config import Config
from ..utils.messages import MessageFormatter

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Notification service class for handling automated notifications.
    
    Manages daily summary reports, late alerts, and other scheduled notifications.
    """
    
    def __init__(self, bot_token: str, db: AttendanceDatabase, message_formatter: MessageFormatter):
        """
        Initialize notification service.
        
        Args:
            bot_token: Telegram bot token
            db: Database instance
            message_formatter: Message formatter instance
        """
        self.bot = Bot(token=bot_token)
        self.db = db
        self.message_formatter = message_formatter
        self.is_running = False
        
        logger.info("Notification service initialized")
    
    async def run_scheduler(self) -> None:
        """
        Run the notification scheduler.
        
        This method runs continuously and checks for scheduled notifications.
        """
        self.is_running = True
        logger.info("Notification scheduler started")
        
        while self.is_running:
            try:
                current_time = datetime.now()
                current_hour = current_time.hour
                current_minute = current_time.minute
                
                # Daily summary at 8 PM (20:00)
                if current_hour == 20 and current_minute == 0:
                    await self._send_daily_summary()
                
                # Late check-in reminders at 9:30 AM (optional)
                elif current_hour == 9 and current_minute == 30:
                    await self._send_late_reminders()
                
                # Missed checkout reminders at 6 PM (18:00)
                elif current_hour == 18 and current_minute == 0:
                    await self._send_missed_checkout_reminders()
                
                # Health check ping (if enabled) - every 14 minutes
                elif current_minute % 14 == 0 and Config.ENABLE_SERVER_WAKEUP:
                    await self._send_health_ping()
                
                # Wait 60 seconds before next check
                await asyncio.sleep(60)
                
            except asyncio.CancelledError:
                logger.info("Notification scheduler cancelled")
                break
            except Exception as e:
                logger.error(f"Error in notification scheduler: {e}")
                await asyncio.sleep(60)  # Continue after error
        
        self.is_running = False
        logger.info("Notification scheduler stopped")
    
    def stop(self) -> None:
        """Stop the notification scheduler."""
        self.is_running = False
        logger.info("Notification scheduler stop requested")
    
    async def _send_daily_summary(self) -> None:
        """Send daily summary to all admins."""
        try:
            logger.info("Sending daily summary to admins")
            
            # Get summary data
            summary_data = self.db.get_daily_summary()
            summary_message = self.message_formatter.format_daily_summary(summary_data)
            
            # Get all admins
            admins = self.db.get_all_admins_for_daily_summary()
            
            if not admins:
                logger.warning("No admins found for daily summary")
                return
            
            # Send to each admin
            success_count = 0
            for admin_id in admins:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=summary_message,
                        parse_mode='Markdown'
                    )
                    success_count += 1
                    logger.info(f"Daily summary sent to admin {admin_id}")
                    
                    # Log notification
                    self.db.log_notification(admin_id, 'daily_summary', 'Daily summary sent')
                    
                except Exception as e:
                    logger.error(f"Failed to send daily summary to admin {admin_id}: {e}")
            
            logger.info(f"Daily summary sent to {success_count}/{len(admins)} admins")
            
            # Log activity
            self.db.log_server_activity(
                'daily_summary', 
                f'Daily summary sent to {success_count} admins'
            )
            
        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")
    
    async def _send_late_reminders(self) -> None:
        """Send reminders to employees who haven't checked in by 9:30 AM."""
        try:
            logger.info("Checking for late employees")
            
            # Get employees who should have checked in by now
            all_employees = self.db.get_all_employees()
            late_employees = []
            
            for employee in all_employees:
                telegram_id = employee[0]
                status = self.db.get_attendance_status(telegram_id)
                
                # If no check-in today, they're late
                if not status or not status[0]:  # No check_in_time
                    late_employees.append(employee)
            
            if not late_employees:
                logger.info("No late employees found")
                return
            
            # Send reminders
            reminder_message = (
                "⏰ **Attendance Reminder**\n\n"
                "You haven't checked in today yet. Please share your location "
                "using the 'Check In' button to record your attendance.\n\n"
                "🔒 Location sharing is required for security."
            )
            
            success_count = 0
            for employee in late_employees:
                telegram_id = employee[0]
                first_name = employee[2]
                
                try:
                    personalized_message = f"Good morning {first_name}!\n\n{reminder_message}"
                    
                    await self.bot.send_message(
                        chat_id=telegram_id,
                        text=personalized_message,
                        parse_mode='Markdown'
                    )
                    success_count += 1
                    
                    # Log notification
                    self.db.log_notification(telegram_id, 'late_reminder', 'Late check-in reminder sent')
                    
                except Exception as e:
                    logger.error(f"Failed to send reminder to employee {telegram_id}: {e}")
            
            logger.info(f"Late reminders sent to {success_count}/{len(late_employees)} employees")
            
        except Exception as e:
            logger.error(f"Error sending late reminders: {e}")
    
    async def _send_missed_checkout_reminders(self) -> None:
        """Send reminders to employees who haven't checked out by 6 PM."""
        try:
            logger.info("Checking for employees who haven't checked out")
            
            # Get employees who checked in but haven't checked out
            all_employees = self.db.get_all_employees()
            missed_checkout_employees = []
            
            for employee in all_employees:
                telegram_id = employee[0]
                status = self.db.get_attendance_status(telegram_id)
                
                # If checked in but not checked out
                if status and status[0] and not status[1]:  # check_in_time exists, check_out_time doesn't
                    missed_checkout_employees.append(employee)
            
            if not missed_checkout_employees:
                logger.info("No employees with missed checkout found")
                return
            
            # Send reminders
            reminder_message = (
                "🏁 **Check-Out Reminder**\n\n"
                "Don't forget to check out before leaving! Please share your "
                "location using the 'Check Out' button to complete your workday.\n\n"
                "🔒 Location sharing is required for security."
            )
            
            success_count = 0
            for employee in missed_checkout_employees:
                telegram_id = employee[0]
                first_name = employee[2]
                
                try:
                    personalized_message = f"Hi {first_name}!\n\n{reminder_message}"
                    
                    await self.bot.send_message(
                        chat_id=telegram_id,
                        text=personalized_message,
                        parse_mode='Markdown'
                    )
                    success_count += 1
                    
                    # Log notification
                    self.db.log_notification(telegram_id, 'checkout_reminder', 'Check-out reminder sent')
                    
                except Exception as e:
                    logger.error(f"Failed to send checkout reminder to employee {telegram_id}: {e}")
            
            logger.info(f"Checkout reminders sent to {success_count}/{len(missed_checkout_employees)} employees")
            
        except Exception as e:
            logger.error(f"Error sending checkout reminders: {e}")
    
    async def _send_health_ping(self) -> None:
        """Send a health ping to keep server awake (for Render free tier)."""
        try:
            if not Config.SERVER_URL:
                return
            
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{Config.SERVER_URL}/health", timeout=30) as response:
                        if response.status == 200:
                            logger.debug("Health ping successful")
                            self.db.log_server_activity('health_ping', 'Server health ping successful')
                        else:
                            logger.warning(f"Health ping returned status {response.status}")
                            
                except asyncio.TimeoutError:
                    logger.warning("Health ping timed out")
                except Exception as e:
                    logger.warning(f"Health ping failed: {e}")
                    
        except Exception as e:
            logger.error(f"Error in health ping: {e}")
    
    async def send_late_alert_to_admins(self, employee_id: int, employee_name: str, 
                                      check_in_time: str, reason: Optional[str] = None) -> None:
        """
        Send late arrival alert to admins.
        
        Args:
            employee_id: Employee Telegram ID
            employee_name: Employee name
            check_in_time: Check-in time string
            reason: Reason for being late (if provided)
        """
        try:
            message = f"🕐 **Late Arrival Alert**\n\n"
            message += f"**Employee:** {employee_name}\n"
            message += f"**ID:** `{employee_id}`\n"
            message += f"**Check-in Time:** {check_in_time}\n"
            
            if reason:
                message += f"**Reason:** {reason}\n"
            else:
                message += f"**Reason:** Not provided\n"
            
            message += f"\n⚠️ This employee checked in after the standard work start time."
            
            # Get all admins
            admins = self.db.get_all_admins()
            
            success_count = 0
            for admin_id in admins:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    success_count += 1
                    
                    # Log notification
                    self.db.log_notification(admin_id, 'late_alert', f'Late alert for employee {employee_id}')
                    
                except Exception as e:
                    logger.error(f"Failed to send late alert to admin {admin_id}: {e}")
            
            logger.info(f"Late alert sent to {success_count} admins for employee {employee_id}")
            
        except Exception as e:
            logger.error(f"Error sending late alert: {e}")
    
    async def send_early_departure_alert_to_admins(self, employee_id: int, employee_name: str,
                                                 check_out_time: str, reason: Optional[str] = None) -> None:
        """
        Send early departure alert to admins.
        
        Args:
            employee_id: Employee Telegram ID
            employee_name: Employee name
            check_out_time: Check-out time string
            reason: Reason for early departure (if provided)
        """
        try:
            message = f"🕕 **Early Departure Alert**\n\n"
            message += f"**Employee:** {employee_name}\n"
            message += f"**ID:** `{employee_id}`\n"
            message += f"**Check-out Time:** {check_out_time}\n"
            
            if reason:
                message += f"**Reason:** {reason}\n"
            else:
                message += f"**Reason:** Not provided\n"
            
            message += f"\n⚠️ This employee checked out before the standard work end time."
            
            # Get all admins
            admins = self.db.get_all_admins()
            
            success_count = 0
            for admin_id in admins:
                try:
                    await self.bot.send_message(
                        chat_id=admin_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    success_count += 1
                    
                    # Log notification
                    self.db.log_notification(admin_id, 'early_departure_alert', f'Early departure alert for employee {employee_id}')
                    
                except Exception as e:
                    logger.error(f"Failed to send early departure alert to admin {admin_id}: {e}")
            
            logger.info(f"Early departure alert sent to {success_count} admins for employee {employee_id}")
            
        except Exception as e:
            logger.error(f"Error sending early departure alert: {e}")
    
    async def send_admin_notification(self, admin_id: int, message: str, notification_type: str = "general") -> bool:
        """
        Send notification to specific admin.
        
        Args:
            admin_id: Admin Telegram ID
            message: Message to send
            notification_type: Type of notification for logging
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            await self.bot.send_message(
                chat_id=admin_id,
                text=message,
                parse_mode='Markdown'
            )
            
            # Log notification
            self.db.log_notification(admin_id, notification_type, message[:100])
            
            logger.info(f"Notification sent to admin {admin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification to admin {admin_id}: {e}")
            return False
    
    async def broadcast_to_all_employees(self, message: str, notification_type: str = "broadcast") -> int:
        """
        Broadcast message to all registered employees.
        
        Args:
            message: Message to broadcast
            notification_type: Type of notification for logging
            
        Returns:
            int: Number of successful sends
        """
        try:
            employees = self.db.get_all_employees()
            success_count = 0
            
            for employee in employees:
                telegram_id = employee[0]
                
                try:
                    await self.bot.send_message(
                        chat_id=telegram_id,
                        text=message,
                        parse_mode='Markdown'
                    )
                    success_count += 1
                    
                    # Log notification
                    self.db.log_notification(telegram_id, notification_type, message[:100])
                    
                except Exception as e:
                    logger.error(f"Failed to send broadcast to employee {telegram_id}: {e}")
            
            logger.info(f"Broadcast sent to {success_count}/{len(employees)} employees")
            return success_count
            
        except Exception as e:
            logger.error(f"Error in broadcast: {e}")
            return 0 