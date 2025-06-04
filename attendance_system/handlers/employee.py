"""
Employee handlers module for the Enhanced Attendance System.

This module contains all Telegram bot handlers for employee interactions.
"""

import logging
from datetime import datetime
from typing import Optional

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from ..core.database import AttendanceDatabase
from ..core.config import Config
from ..utils.location import LocationValidator
from ..utils.keyboards import KeyboardBuilder
from ..utils.messages import MessageFormatter

logger = logging.getLogger(__name__)


class EmployeeHandlers:
    """
    Employee handler class for managing employee interactions.
    
    Handles all employee-related commands and messages including
    registration, check-in/out, status queries, and reports.
    """
    
    def __init__(self, db: AttendanceDatabase, message_formatter: MessageFormatter):
        """
        Initialize employee handlers.
        
        Args:
            db: Database instance
            message_formatter: Message formatter instance
        """
        self.db = db
        self.message_formatter = message_formatter
        self.location_validator = LocationValidator()
        self.keyboard_builder = KeyboardBuilder()
        
        logger.info("Employee handlers initialized")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user = update.effective_user
        
        if not self.db.is_employee_registered(user.id):
            welcome_message = self.message_formatter.format_welcome_message(
                user.first_name, is_registered=False
            )
            keyboard = self.keyboard_builder.get_registration_keyboard()
            
            await update.message.reply_text(
                welcome_message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            # Check current status
            status = self.db.get_attendance_status(user.id)
            is_checked_in = status and status[2] == 'checked_in'
            
            welcome_message = self.message_formatter.format_welcome_message(
                user.first_name, is_registered=True
            )
            keyboard = self.keyboard_builder.get_location_keyboard(is_checked_in)
            
            await update.message.reply_text(
                welcome_message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        
        logger.info(f"Start command processed for user {user.id}")
    
    async def register_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /register command."""
        user = update.effective_user
        
        if self.db.is_employee_registered(user.id):
            await update.message.reply_text("✅ You are already registered!")
            return
        
        keyboard = self.keyboard_builder.get_contact_keyboard()
        await update.message.reply_text(
            "📝 Please share your contact information by clicking the 'Share Contact' button below.",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        logger.info(f"Register command processed for user {user.id}")
    
    async def handle_contact(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle contact sharing for registration."""
        user = update.effective_user
        contact = update.message.contact
        
        # Register the employee
        success = self.db.register_employee(
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=contact.phone_number
        )
        
        if success:
            keyboard = self.keyboard_builder.get_location_keyboard(False)
            await update.message.reply_text(
                "✅ **Registration Successful!**\n\n"
                "Welcome to the Enhanced Attendance System!\n"
                "You can now use the location sharing buttons to check in and out.",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            logger.info(f"Employee {user.id} registered successfully")
        else:
            await update.message.reply_text(
                "❌ Registration failed. Please try again later."
            )
            logger.error(f"Failed to register employee {user.id}")
    
    async def handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle location sharing for check-in/check-out."""
        user = update.effective_user
        location = update.message.location
        
        if not self.db.is_employee_registered(user.id):
            error_message = self.message_formatter.format_error_message("not_registered")
            await update.message.reply_text(error_message, parse_mode='Markdown')
            return
        
        # Validate location
        is_within_radius, distance = self.location_validator.is_within_office_radius(
            location.latitude, location.longitude
        )
        
        if not is_within_radius:
            denial_message = self.message_formatter.format_location_denied_message(distance)
            await update.message.reply_text(denial_message, parse_mode='Markdown')
            return
        
        # Check current status to determine check-in or check-out
        status = self.db.get_attendance_status(user.id)
        
        if not status or status[2] == 'checked_out':
            await self._handle_checkin(update, location, distance)
        elif status[2] == 'checked_in':
            await self._handle_checkout(update, location, distance, status)
    
    async def _handle_checkin(self, update: Update, location, distance: float) -> None:
        """Handle check-in process."""
        user = update.effective_user
        
        # Check if this would be a late check-in
        is_late = self.db._is_late_checkin(user.id, datetime.now(self.db.timezone))
        
        if is_late:
            # Set conversation state to expect late reason
            self.db.set_conversation_state(
                user.id, 
                'waiting_late_reason', 
                f"{location.latitude},{location.longitude},{distance}"
            )
            
            # Get work hours for context
            work_start, _ = self.db.get_effective_work_hours(user.id, datetime.now(self.db.timezone).date())
            current_time = datetime.now(self.db.timezone).strftime('%H:%M')
            
            prompt_message = self.message_formatter.format_conversation_prompt(
                'late_reason', 
                {'work_start': work_start, 'current_time': current_time}
            )
            
            await update.message.reply_text(prompt_message, parse_mode='Markdown')
            return
        
        # Normal check-in (not late)
        success, message, is_late = self.db.check_in(
            user.id, location.latitude, location.longitude, distance
        )
        
        if success:
            time_str = message.split('at ')[1]
            success_message = self.message_formatter.format_check_in_success(
                time_str, distance, is_late
            )
            keyboard = self.keyboard_builder.get_location_keyboard(True)
            
            await update.message.reply_text(
                success_message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ {message}")
        
        logger.info(f"Check-in processed for user {user.id} - Success: {success}")
    
    async def _handle_checkout(self, update: Update, location, distance: float, status) -> None:
        """Handle check-out process."""
        user = update.effective_user
        
        # Check if this would be an early check-out
        is_early = self.db._is_early_checkout(user.id, datetime.now(self.db.timezone))
        
        if is_early:
            # Set conversation state to expect early checkout reason
            self.db.set_conversation_state(
                user.id,
                'waiting_early_reason',
                f"{location.latitude},{location.longitude},{distance}"
            )
            
            # Get work hours for context
            _, work_end = self.db.get_effective_work_hours(user.id, datetime.now(self.db.timezone).date())
            current_time = datetime.now(self.db.timezone).strftime('%H:%M')
            
            prompt_message = self.message_formatter.format_conversation_prompt(
                'early_reason',
                {'work_end': work_end, 'current_time': current_time}
            )
            
            await update.message.reply_text(prompt_message, parse_mode='Markdown')
            return
        
        # Normal check-out (not early)
        success, message, is_early = self.db.check_out(
            user.id, location.latitude, location.longitude, distance
        )
        
        if success:
            # Calculate work duration
            check_in_time = datetime.fromisoformat(status[0])
            check_out_time = datetime.now(self.db.timezone)
            work_duration = check_out_time - check_in_time
            time_str = message.split('at ')[1]
            
            success_message = self.message_formatter.format_check_out_success(
                time_str, distance, work_duration, is_early
            )
            keyboard = self.keyboard_builder.get_location_keyboard(False)
            
            await update.message.reply_text(
                success_message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ {message}")
        
        logger.info(f"Check-out processed for user {user.id} - Success: {success}")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle text messages based on conversation state."""
        user = update.effective_user
        text = update.message.text
        
        # Check conversation state
        state, data = self.db.get_conversation_state(user.id)
        
        if state == 'waiting_late_reason':
            await self._process_late_reason(update, text, data)
        elif state == 'waiting_early_reason':
            await self._process_early_reason(update, text, data)
        elif text in ["🟢 Check In", "🔴 Check Out"]:
            # If user tries to use text buttons instead of location
            error_message = self.message_formatter.format_error_message("location_required")
            await update.message.reply_text(error_message, parse_mode='Markdown')
        else:
            await self._handle_other_commands(update, text)
    
    async def _process_late_reason(self, update: Update, reason: str, location_data: str) -> None:
        """Process late check-in reason."""
        user = update.effective_user
        lat_str, lon_str, distance_str = location_data.split(',')
        
        latitude = float(lat_str)
        longitude = float(lon_str)
        distance = float(distance_str)
        
        # Perform check-in with reason
        success, message, is_late = self.db.check_in(
            user.id, latitude, longitude, distance, reason
        )
        
        # Clear conversation state
        self.db.clear_conversation_state(user.id)
        
        if success:
            time_str = message.split('at ')[1]
            success_message = self.message_formatter.format_check_in_success(
                time_str, distance, is_late, reason
            )
            keyboard = self.keyboard_builder.get_location_keyboard(True)
            
            await update.message.reply_text(
                success_message,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ {message}")
        
        logger.info(f"Late check-in with reason processed for user {user.id}")
    
    async def _process_early_reason(self, update: Update, reason: str, location_data: str) -> None:
        """Process early check-out reason."""
        user = update.effective_user
        lat_str, lon_str, distance_str = location_data.split(',')
        
        latitude = float(lat_str)
        longitude = float(lon_str)
        distance = float(distance_str)
        
        # Perform check-out with reason
        success, message, is_early = self.db.check_out(
            user.id, latitude, longitude, distance, reason
        )
        
        # Clear conversation state
        self.db.clear_conversation_state(user.id)
        
        if success:
            # Calculate work duration from status
            status = self.db.get_attendance_status(user.id)
            if status:
                check_in_time = datetime.fromisoformat(status[0])
                check_out_time = datetime.now(self.db.timezone)
                work_duration = check_out_time - check_in_time
                time_str = message.split('at ')[1]
                
                success_message = self.message_formatter.format_check_out_success(
                    time_str, distance, work_duration, is_early, reason
                )
                keyboard = self.keyboard_builder.get_location_keyboard(False)
                
                await update.message.reply_text(
                    success_message,
                    reply_markup=keyboard,
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(f"❌ {message}")
        
        logger.info(f"Early check-out with reason processed for user {user.id}")
    
    async def _handle_other_commands(self, update: Update, text: str) -> None:
        """Handle other commands like status, reports, etc."""
        if text == "📊 My Status":
            await self.status_command(update, None)
        elif text == "📈 My Report":
            await self.report_command(update, None)
        elif text == "ℹ️ Help":
            user = update.effective_user
            is_admin = self.db.is_admin(user.id)
            help_message = self.message_formatter.format_help_message(is_admin, True)
            await update.message.reply_text(help_message, parse_mode='Markdown')
        else:
            await update.message.reply_text(
                "❓ **Unknown Command**\n\n"
                "Please use the buttons provided or type /help for assistance.",
                parse_mode='Markdown'
            )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show current attendance status."""
        user = update.effective_user
        status = self.db.get_attendance_status(user.id)
        today = datetime.now(self.db.timezone).date().strftime('%Y-%m-%d')
        
        if status:
            status_data = {
                'check_in_time': status[0],
                'check_out_time': status[1],
                'is_late': status[3],
                'is_early_checkout': status[4]
            }
        else:
            status_data = None
        
        status_message = self.message_formatter.format_attendance_status(status_data, today)
        await update.message.reply_text(status_message, parse_mode='Markdown')
    
    async def report_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show attendance report for last 7 days."""
        user = update.effective_user
        
        # This would typically fetch recent attendance records
        # For now, just show current status
        await self.status_command(update, context)
        
        logger.info(f"Report command processed for user {user.id}") 