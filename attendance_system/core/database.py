"""
Database module for the Enhanced Attendance System.

This module handles all database operations including schema management,
employee records, attendance tracking, and admin functions.
"""

import sqlite3
import logging
from datetime import datetime, time, date
from typing import Optional, List, Tuple, Dict, Any
import pytz

from .config import Config

logger = logging.getLogger(__name__)


class AttendanceDatabase:
    """
    Enhanced database class for attendance management.
    
    Handles all database operations with proper error handling,
    logging, and data validation.
    """
    
    def __init__(self, db_name: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            db_name: Database file name. Uses config default if None.
        """
        self.db_name = db_name or Config.DATABASE_NAME
        self.timezone = pytz.timezone(Config.TIMEZONE)
        self._initialize_database()
        logger.info(f"Database initialized: {self.db_name}")
    
    def _initialize_database(self) -> None:
        """Initialize database schema with all required tables."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Create all tables
            self._create_employees_table(cursor)
            self._create_attendance_table(cursor)
            self._create_admins_table(cursor)
            self._create_exceptional_hours_table(cursor)
            self._create_conversation_state_table(cursor)
            self._create_notification_log_table(cursor)
            self._create_server_activity_table(cursor)
            
            # Create indexes for better performance
            self._create_indexes(cursor)
            
            conn.commit()
            logger.info("Database schema initialized successfully")
    
    def _create_employees_table(self, cursor: sqlite3.Cursor) -> None:
        """Create employees table with all required fields."""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                last_name TEXT,
                phone_number TEXT,
                is_active BOOLEAN DEFAULT 1,
                reminder_enabled BOOLEAN DEFAULT 1,
                reminder_time TEXT DEFAULT '09:00',
                checkout_reminder_enabled BOOLEAN DEFAULT 1,
                checkout_reminder_time TEXT DEFAULT '17:00',
                standard_work_start TEXT DEFAULT '09:00',
                standard_work_end TEXT DEFAULT '17:00',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def _create_attendance_table(self, cursor: sqlite3.Cursor) -> None:
        """Create attendance table with enhanced tracking."""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                check_in_time TIMESTAMP,
                check_out_time TIMESTAMP,
                check_in_latitude REAL,
                check_in_longitude REAL,
                check_out_latitude REAL,
                check_out_longitude REAL,
                check_in_distance REAL,
                check_out_distance REAL,
                late_reason TEXT,
                early_checkout_reason TEXT,
                date DATE NOT NULL,
                status TEXT DEFAULT 'checked_in',
                is_late BOOLEAN DEFAULT 0,
                is_early_checkout BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES employees (telegram_id)
            )
        ''')
    
    def _create_admins_table(self, cursor: sqlite3.Cursor) -> None:
        """Create admins table with permissions."""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                telegram_id INTEGER PRIMARY KEY,
                alert_enabled BOOLEAN DEFAULT 1,
                late_threshold_minutes INTEGER DEFAULT 30,
                receive_daily_summary BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES admins (telegram_id)
            )
        ''')
    
    def _create_exceptional_hours_table(self, cursor: sqlite3.Cursor) -> None:
        """Create exceptional hours table for custom schedules."""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exceptional_hours (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                date DATE NOT NULL,
                work_start_time TEXT NOT NULL,
                work_end_time TEXT NOT NULL,
                reason TEXT,
                created_by INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (telegram_id) REFERENCES employees (telegram_id),
                FOREIGN KEY (created_by) REFERENCES admins (telegram_id),
                UNIQUE(telegram_id, date)
            )
        ''')
    
    def _create_conversation_state_table(self, cursor: sqlite3.Cursor) -> None:
        """Create conversation state table for multi-step interactions."""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_state (
                telegram_id INTEGER PRIMARY KEY,
                state TEXT NOT NULL,
                data TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def _create_notification_log_table(self, cursor: sqlite3.Cursor) -> None:
        """Create notification log table for tracking sent messages."""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                notification_type TEXT NOT NULL,
                message TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                delivery_status TEXT DEFAULT 'sent'
            )
        ''')
    
    def _create_server_activity_table(self, cursor: sqlite3.Cursor) -> None:
        """Create server activity table for monitoring."""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS server_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_type TEXT NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    
    def _create_indexes(self, cursor: sqlite3.Cursor) -> None:
        """Create database indexes for better performance."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_telegram_id ON attendance(telegram_id)",
            "CREATE INDEX IF NOT EXISTS idx_attendance_telegram_date ON attendance(telegram_id, date)",
            "CREATE INDEX IF NOT EXISTS idx_notification_log_date ON notification_log(sent_at)",
            "CREATE INDEX IF NOT EXISTS idx_server_activity_date ON server_activity(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_exceptional_hours_date ON exceptional_hours(telegram_id, date)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
    
    # Employee Management Methods
    def register_employee(self, telegram_id: int, username: Optional[str] = None, 
                         first_name: str = "", last_name: Optional[str] = None, 
                         phone_number: Optional[str] = None) -> bool:
        """
        Register a new employee.
        
        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: Employee first name
            last_name: Employee last name
            phone_number: Employee phone number
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO employees 
                    (telegram_id, username, first_name, last_name, phone_number, updated_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (telegram_id, username, first_name, last_name, phone_number))
                conn.commit()
                
                self.log_server_activity('employee_registered', f'User {telegram_id} registered')
                logger.info(f"Employee registered: {telegram_id} ({first_name})")
                return True
                
        except Exception as e:
            logger.error(f"Error registering employee {telegram_id}: {e}")
            return False
    
    def is_employee_registered(self, telegram_id: int) -> bool:
        """Check if employee is registered and active."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT telegram_id FROM employees 
                    WHERE telegram_id = ? AND is_active = 1
                ''', (telegram_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking employee registration {telegram_id}: {e}")
            return False
    
    def get_employee_info(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Get employee information."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT telegram_id, username, first_name, last_name, phone_number,
                           standard_work_start, standard_work_end, created_at
                    FROM employees WHERE telegram_id = ? AND is_active = 1
                ''', (telegram_id,))
                
                row = cursor.fetchone()
                if row:
                    return {
                        'telegram_id': row[0],
                        'username': row[1],
                        'first_name': row[2],
                        'last_name': row[3],
                        'phone_number': row[4],
                        'work_start': row[5],
                        'work_end': row[6],
                        'created_at': row[7]
                    }
                return None
        except Exception as e:
            logger.error(f"Error getting employee info {telegram_id}: {e}")
            return None
    
    # Attendance Management Methods
    def check_in(self, telegram_id: int, latitude: float, longitude: float, 
                distance: float, late_reason: Optional[str] = None) -> Tuple[bool, str, bool]:
        """
        Record employee check-in.
        
        Args:
            telegram_id: Employee Telegram ID
            latitude: Check-in latitude
            longitude: Check-in longitude
            distance: Distance from office
            late_reason: Reason if checking in late
            
        Returns:
            Tuple of (success, message, is_late)
        """
        try:
            current_time = datetime.now(self.timezone)
            current_date = current_time.date()
            
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Check if already checked in today
                cursor.execute('''
                    SELECT id FROM attendance 
                    WHERE telegram_id = ? AND date = ? AND check_out_time IS NULL
                ''', (telegram_id, current_date))
                
                if cursor.fetchone():
                    return False, "You are already checked in today!", False
                
                # Check if this is a late check-in
                is_late = self._is_late_checkin(telegram_id, current_time)
                
                # Insert attendance record
                cursor.execute('''
                    INSERT INTO attendance 
                    (telegram_id, check_in_time, check_in_latitude, check_in_longitude, 
                     check_in_distance, date, status, is_late, late_reason)
                    VALUES (?, ?, ?, ?, ?, ?, 'checked_in', ?, ?)
                ''', (telegram_id, current_time, latitude, longitude, distance, 
                      current_date, is_late, late_reason))
                
                conn.commit()
                
                # Log activity
                activity_detail = f"Distance: {distance:.0f}m"
                if is_late and late_reason:
                    activity_detail += f", Late reason: {late_reason}"
                self.log_server_activity('check_in', activity_detail)
                
                message = f"Check-in successful at {current_time.strftime('%H:%M:%S')}"
                logger.info(f"Employee {telegram_id} checked in - {activity_detail}")
                
                return True, message, is_late
                
        except Exception as e:
            logger.error(f"Error during check-in for {telegram_id}: {e}")
            return False, f"Check-in failed: {str(e)}", False
    
    def check_out(self, telegram_id: int, latitude: float, longitude: float, 
                 distance: float, early_reason: Optional[str] = None) -> Tuple[bool, str, bool]:
        """
        Record employee check-out.
        
        Args:
            telegram_id: Employee Telegram ID
            latitude: Check-out latitude
            longitude: Check-out longitude
            distance: Distance from office
            early_reason: Reason if checking out early
            
        Returns:
            Tuple of (success, message, is_early)
        """
        try:
            current_time = datetime.now(self.timezone)
            current_date = current_time.date()
            
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Find today's check-in record
                cursor.execute('''
                    SELECT id FROM attendance 
                    WHERE telegram_id = ? AND date = ? AND check_out_time IS NULL
                ''', (telegram_id, current_date))
                
                record = cursor.fetchone()
                if not record:
                    return False, "You haven't checked in today or already checked out!", False
                
                # Check if this is an early check-out
                is_early = self._is_early_checkout(telegram_id, current_time)
                
                # Update attendance record
                cursor.execute('''
                    UPDATE attendance 
                    SET check_out_time = ?, check_out_latitude = ?, check_out_longitude = ?, 
                        check_out_distance = ?, status = 'checked_out', 
                        is_early_checkout = ?, early_checkout_reason = ?
                    WHERE id = ?
                ''', (current_time, latitude, longitude, distance, is_early, early_reason, record[0]))
                
                conn.commit()
                
                # Log activity
                activity_detail = f"Distance: {distance:.0f}m"
                if is_early and early_reason:
                    activity_detail += f", Early reason: {early_reason}"
                self.log_server_activity('check_out', activity_detail)
                
                message = f"Check-out successful at {current_time.strftime('%H:%M:%S')}"
                logger.info(f"Employee {telegram_id} checked out - {activity_detail}")
                
                return True, message, is_early
                
        except Exception as e:
            logger.error(f"Error during check-out for {telegram_id}: {e}")
            return False, f"Check-out failed: {str(e)}", False
    
    def get_attendance_status(self, telegram_id: int, date_obj: Optional[date] = None) -> Optional[Tuple]:
        """Get current attendance status for a specific date."""
        try:
            if date_obj is None:
                date_obj = datetime.now(self.timezone).date()
            
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT check_in_time, check_out_time, status, is_late, is_early_checkout,
                           late_reason, early_checkout_reason
                    FROM attendance 
                    WHERE telegram_id = ? AND date = ?
                ''', (telegram_id, date_obj))
                
                return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting attendance status for {telegram_id}: {e}")
            return None
    
    def _is_late_checkin(self, telegram_id: int, checkin_time: datetime) -> bool:
        """Check if check-in is late based on work hours."""
        work_start, _ = self.get_effective_work_hours(telegram_id, checkin_time.date())
        work_start_time = datetime.strptime(work_start, '%H:%M').time()
        return checkin_time.time() > work_start_time
    
    def _is_early_checkout(self, telegram_id: int, checkout_time: datetime) -> bool:
        """Check if check-out is early based on work hours."""
        _, work_end = self.get_effective_work_hours(telegram_id, checkout_time.date())
        work_end_time = datetime.strptime(work_end, '%H:%M').time()
        return checkout_time.time() < work_end_time
    
    def get_effective_work_hours(self, telegram_id: int, date_obj: date) -> Tuple[str, str]:
        """Get effective work hours (exceptional or standard)."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Check for exceptional hours first
                cursor.execute('''
                    SELECT work_start_time, work_end_time FROM exceptional_hours
                    WHERE telegram_id = ? AND date = ?
                ''', (telegram_id, date_obj))
                
                exceptional = cursor.fetchone()
                if exceptional:
                    return exceptional[0], exceptional[1]
                
                # Get standard work hours
                cursor.execute('''
                    SELECT standard_work_start, standard_work_end FROM employees
                    WHERE telegram_id = ?
                ''', (telegram_id,))
                
                standard = cursor.fetchone()
                if standard:
                    return standard[0], standard[1]
                    
                # Default fallback
                return Config.DEFAULT_WORK_START, Config.DEFAULT_WORK_END
                
        except Exception as e:
            logger.error(f"Error getting work hours for {telegram_id}: {e}")
            return Config.DEFAULT_WORK_START, Config.DEFAULT_WORK_END
    
    # Admin Management Methods
    def add_admin(self, telegram_id: int, created_by: Optional[int] = None) -> bool:
        """Add a new admin."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO admins (telegram_id, created_by)
                    VALUES (?, ?)
                ''', (telegram_id, created_by))
                conn.commit()
                
                self.log_server_activity('admin_added', f'Admin {telegram_id} added')
                logger.info(f"Admin added: {telegram_id}")
                return True
        except Exception as e:
            logger.error(f"Error adding admin {telegram_id}: {e}")
            return False
    
    def is_admin(self, telegram_id: int) -> bool:
        """Check if user is admin."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT telegram_id FROM admins WHERE telegram_id = ?
                ''', (telegram_id,))
                return cursor.fetchone() is not None
        except Exception as e:
            logger.error(f"Error checking admin status for {telegram_id}: {e}")
            return False
    
    def get_all_admins(self) -> List[int]:
        """Get all admin IDs."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT telegram_id FROM admins')
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting all admins: {e}")
            return []
    
    # Exceptional Hours Management
    def add_exceptional_hours(self, telegram_id: int, date_obj: date, 
                            work_start: str, work_end: str, 
                            reason: str, created_by: int) -> bool:
        """Add exceptional working hours for an employee."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO exceptional_hours
                    (telegram_id, date, work_start_time, work_end_time, reason, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (telegram_id, date_obj, work_start, work_end, reason, created_by))
                conn.commit()
                
                self.log_server_activity('exceptional_hours_added', 
                                       f'Employee {telegram_id}, Date {date_obj}, Hours {work_start}-{work_end}')
                logger.info(f"Exceptional hours added for {telegram_id} on {date_obj}")
                return True
        except Exception as e:
            logger.error(f"Error adding exceptional hours: {e}")
            return False
    
    # Conversation State Management
    def set_conversation_state(self, telegram_id: int, state: str, 
                             data: Optional[str] = None, expires_minutes: int = 30) -> None:
        """Set conversation state for multi-step interactions."""
        try:
            expires_at = datetime.now() + datetime.timedelta(minutes=expires_minutes)
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO conversation_state 
                    (telegram_id, state, data, expires_at, updated_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (telegram_id, state, data, expires_at))
                conn.commit()
        except Exception as e:
            logger.error(f"Error setting conversation state for {telegram_id}: {e}")
    
    def get_conversation_state(self, telegram_id: int) -> Tuple[Optional[str], Optional[str]]:
        """Get conversation state."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT state, data FROM conversation_state 
                    WHERE telegram_id = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
                ''', (telegram_id,))
                result = cursor.fetchone()
                return result if result else (None, None)
        except Exception as e:
            logger.error(f"Error getting conversation state for {telegram_id}: {e}")
            return None, None
    
    def clear_conversation_state(self, telegram_id: int) -> None:
        """Clear conversation state."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM conversation_state WHERE telegram_id = ?', (telegram_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Error clearing conversation state for {telegram_id}: {e}")
    
    # Logging and Monitoring
    def log_notification(self, telegram_id: int, notification_type: str, 
                        message: str, delivery_status: str = 'sent') -> None:
        """Log notification sent to database."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO notification_log 
                    (telegram_id, notification_type, message, delivery_status)
                    VALUES (?, ?, ?, ?)
                ''', (telegram_id, notification_type, message, delivery_status))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging notification: {e}")
    
    def log_server_activity(self, activity_type: str, details: Optional[str] = None) -> None:
        """Log server activity for monitoring."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO server_activity (activity_type, details)
                    VALUES (?, ?)
                ''', (activity_type, details))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging server activity: {e}")
    
    # Reporting and Analytics
    def get_daily_summary(self, date_obj: Optional[date] = None) -> Dict[str, Any]:
        """Get daily attendance summary for reports."""
        if date_obj is None:
            date_obj = datetime.now(self.timezone).date()
        
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Get total employees
                cursor.execute('SELECT COUNT(*) FROM employees WHERE is_active = 1')
                total_employees = cursor.fetchone()[0]
                
                # Get attendance stats
                cursor.execute('''
                    SELECT 
                        COUNT(*) as checked_in,
                        SUM(CASE WHEN check_out_time IS NOT NULL THEN 1 ELSE 0 END) as checked_out,
                        SUM(CASE WHEN is_late = 1 THEN 1 ELSE 0 END) as late_checkins,
                        SUM(CASE WHEN is_early_checkout = 1 THEN 1 ELSE 0 END) as early_checkouts
                    FROM attendance 
                    WHERE date = ?
                ''', (date_obj,))
                
                stats = cursor.fetchone()
                
                return {
                    'date': date_obj,
                    'total_employees': total_employees,
                    'checked_in': stats[0],
                    'checked_out': stats[1],
                    'late_checkins': stats[2],
                    'early_checkouts': stats[3],
                    'attendance_rate': (stats[0] / total_employees * 100) if total_employees > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Error getting daily summary: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> None:
        """Clean up old data to maintain database performance."""
        try:
            cutoff_date = datetime.now().date() - datetime.timedelta(days=days_to_keep)
            
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Clean old notification logs
                cursor.execute('''
                    DELETE FROM notification_log 
                    WHERE sent_at < ?
                ''', (cutoff_date,))
                
                # Clean old server activity logs
                cursor.execute('''
                    DELETE FROM server_activity 
                    WHERE timestamp < ?
                ''', (cutoff_date,))
                
                # Clean expired conversation states
                cursor.execute('''
                    DELETE FROM conversation_state 
                    WHERE expires_at < CURRENT_TIMESTAMP
                ''', )
                
                conn.commit()
                logger.info(f"Database cleanup completed - removed data older than {cutoff_date}")
                
        except Exception as e:
            logger.error(f"Error during database cleanup: {e}") 