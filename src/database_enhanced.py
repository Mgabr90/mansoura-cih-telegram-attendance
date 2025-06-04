import sqlite3
import os
from datetime import datetime, timedelta, time
import pytz
import csv
import io

class EnhancedAttendanceDatabase:
    def __init__(self, db_name='attendance.db'):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Employees table (enhanced)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    telegram_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    phone_number TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    reminder_enabled BOOLEAN DEFAULT 1,
                    reminder_time TEXT DEFAULT '09:00',
                    checkout_reminder_enabled BOOLEAN DEFAULT 1,
                    checkout_reminder_time TEXT DEFAULT '17:00',
                    standard_work_start TEXT DEFAULT '09:00',
                    standard_work_end TEXT DEFAULT '17:00',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Attendance records table (enhanced)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER,
                    check_in_time TIMESTAMP,
                    check_out_time TIMESTAMP,
                    check_in_latitude REAL,
                    check_in_longitude REAL,
                    check_out_latitude REAL,
                    check_out_longitude REAL,
                    check_in_location_note TEXT,
                    check_out_location_note TEXT,
                    late_reason TEXT,
                    early_checkout_reason TEXT,
                    date DATE,
                    status TEXT DEFAULT 'checked_in',
                    is_late BOOLEAN DEFAULT 0,
                    is_early_checkout BOOLEAN DEFAULT 0,
                    FOREIGN KEY (telegram_id) REFERENCES employees (telegram_id)
                )
            ''')
            
            # Exceptional working hours table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS exceptional_hours (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER,
                    date DATE,
                    work_start_time TEXT,
                    work_end_time TEXT,
                    reason TEXT,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (telegram_id) REFERENCES employees (telegram_id),
                    FOREIGN KEY (created_by) REFERENCES admins (telegram_id)
                )
            ''')
            
            # Conversation state table for handling multi-step interactions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_state (
                    telegram_id INTEGER PRIMARY KEY,
                    state TEXT,
                    data TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add new columns to existing tables if they don't exist
            new_columns = [
                ('employees', 'standard_work_start', 'TEXT DEFAULT "09:00"'),
                ('employees', 'standard_work_end', 'TEXT DEFAULT "17:00"'),
                ('attendance', 'late_reason', 'TEXT'),
                ('attendance', 'early_checkout_reason', 'TEXT'),
                ('attendance', 'is_late', 'BOOLEAN DEFAULT 0'),
                ('attendance', 'is_early_checkout', 'BOOLEAN DEFAULT 0'),
            ]
            
            for table, column, definition in new_columns:
                try:
                    cursor.execute(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
                except sqlite3.OperationalError:
                    pass  # Column already exists
            
            # Admins table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    telegram_id INTEGER PRIMARY KEY,
                    alert_enabled BOOLEAN DEFAULT 1,
                    late_threshold_minutes INTEGER DEFAULT 30,
                    receive_daily_summary BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Notification log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS notification_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER,
                    notification_type TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message TEXT
                )
            ''')
            
            # Server activity log for wake-up purposes
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS server_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    activity_type TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    details TEXT
                )
            ''')
            
            conn.commit()
    
    def set_conversation_state(self, telegram_id, state, data=None):
        """Set conversation state for multi-step interactions"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO conversation_state (telegram_id, state, data, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (telegram_id, state, data))
            conn.commit()
    
    def get_conversation_state(self, telegram_id):
        """Get conversation state"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT state, data FROM conversation_state WHERE telegram_id = ?', (telegram_id,))
            result = cursor.fetchone()
            return result if result else (None, None)
    
    def clear_conversation_state(self, telegram_id):
        """Clear conversation state"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM conversation_state WHERE telegram_id = ?', (telegram_id,))
            conn.commit()
    
    def get_effective_work_hours(self, telegram_id, date=None):
        """Get effective work hours (exceptional or standard)"""
        if date is None:
            date = datetime.now(pytz.timezone('Africa/Cairo')).date()
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Check for exceptional hours first
            cursor.execute('''
                SELECT work_start_time, work_end_time FROM exceptional_hours
                WHERE telegram_id = ? AND date = ?
            ''', (telegram_id, date))
            
            exceptional = cursor.fetchone()
            if exceptional:
                return exceptional[0], exceptional[1]
            
            # Get standard work hours
            cursor.execute('''
                SELECT standard_work_start, standard_work_end FROM employees
                WHERE telegram_id = ?
            ''', (telegram_id,))
            
            standard = cursor.fetchone()
            return standard if standard else ('09:00', '17:00')
    
    def add_exceptional_hours(self, telegram_id, date, work_start, work_end, reason, created_by):
        """Add exceptional working hours for an employee"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO exceptional_hours
                (telegram_id, date, work_start_time, work_end_time, reason, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (telegram_id, date, work_start, work_end, reason, created_by))
            conn.commit()
    
    def is_late_checkin(self, telegram_id, checkin_time=None):
        """Check if check-in is late based on work hours"""
        if checkin_time is None:
            checkin_time = datetime.now(pytz.timezone('Africa/Cairo'))
        
        date = checkin_time.date()
        work_start, _ = self.get_effective_work_hours(telegram_id, date)
        
        work_start_time = datetime.strptime(work_start, '%H:%M').time()
        checkin_time_only = checkin_time.time()
        
        return checkin_time_only > work_start_time
    
    def is_early_checkout(self, telegram_id, checkout_time=None):
        """Check if check-out is early based on work hours"""
        if checkout_time is None:
            checkout_time = datetime.now(pytz.timezone('Africa/Cairo'))
        
        date = checkout_time.date()
        _, work_end = self.get_effective_work_hours(telegram_id, date)
        
        work_end_time = datetime.strptime(work_end, '%H:%M').time()
        checkout_time_only = checkout_time.time()
        
        return checkout_time_only < work_end_time
    
    def check_in_with_reason(self, telegram_id, latitude, longitude, late_reason=None):
        """Enhanced check-in with late reason handling"""
        egypt_tz = pytz.timezone('Africa/Cairo')
        current_time = datetime.now(egypt_tz)
        current_date = current_time.date()
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Check if already checked in today
            cursor.execute('''
                SELECT id FROM attendance 
                WHERE telegram_id = ? AND date = ? AND check_out_time IS NULL
            ''', (telegram_id, current_date))
            
            if cursor.fetchone():
                return False, "You are already checked in today!"
            
            is_late = self.is_late_checkin(telegram_id, current_time)
            
            cursor.execute('''
                INSERT INTO attendance 
                (telegram_id, check_in_time, check_in_latitude, check_in_longitude, 
                 date, status, is_late, late_reason)
                VALUES (?, ?, ?, ?, ?, 'checked_in', ?, ?)
            ''', (telegram_id, current_time, latitude, longitude, current_date, is_late, late_reason))
            conn.commit()
            
            return True, f"Check-in successful at {current_time.strftime('%H:%M:%S')}", is_late
    
    def check_out_with_reason(self, telegram_id, latitude, longitude, early_reason=None):
        """Enhanced check-out with early reason handling"""
        egypt_tz = pytz.timezone('Africa/Cairo')
        current_time = datetime.now(egypt_tz)
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
                return False, "You haven't checked in today or already checked out!"
            
            is_early = self.is_early_checkout(telegram_id, current_time)
            
            cursor.execute('''
                UPDATE attendance 
                SET check_out_time = ?, check_out_latitude = ?, check_out_longitude = ?, 
                    status = 'checked_out', is_early_checkout = ?, early_checkout_reason = ?
                WHERE id = ?
            ''', (current_time, latitude, longitude, is_early, early_reason, record[0]))
            conn.commit()
            
            return True, f"Check-out successful at {current_time.strftime('%H:%M:%S')}", is_early
    
    def get_daily_summary_for_admins(self, date=None):
        """Get daily attendance summary for admin notifications"""
        if date is None:
            date = datetime.now(pytz.timezone('Africa/Cairo')).date()
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Total employees
            cursor.execute('SELECT COUNT(*) FROM employees WHERE is_active = 1')
            total_employees = cursor.fetchone()[0]
            
            # Checked in today
            cursor.execute('''
                SELECT COUNT(*) FROM attendance 
                WHERE date = ? AND check_in_time IS NOT NULL
            ''', (date,))
            checked_in_count = cursor.fetchone()[0]
            
            # Checked out today
            cursor.execute('''
                SELECT COUNT(*) FROM attendance 
                WHERE date = ? AND check_out_time IS NOT NULL
            ''', (date,))
            checked_out_count = cursor.fetchone()[0]
            
            # Late check-ins
            cursor.execute('''
                SELECT COUNT(*) FROM attendance 
                WHERE date = ? AND is_late = 1
            ''', (date,))
            late_count = cursor.fetchone()[0]
            
            # Early check-outs
            cursor.execute('''
                SELECT COUNT(*) FROM attendance 
                WHERE date = ? AND is_early_checkout = 1
            ''', (date,))
            early_checkout_count = cursor.fetchone()[0]
            
            # Late employees with reasons
            cursor.execute('''
                SELECT e.first_name, e.last_name, a.check_in_time, a.late_reason
                FROM attendance a
                JOIN employees e ON a.telegram_id = e.telegram_id
                WHERE a.date = ? AND a.is_late = 1
            ''', (date,))
            late_employees = cursor.fetchall()
            
            # Early checkout employees with reasons
            cursor.execute('''
                SELECT e.first_name, e.last_name, a.check_out_time, a.early_checkout_reason
                FROM attendance a
                JOIN employees e ON a.telegram_id = e.telegram_id
                WHERE a.date = ? AND a.is_early_checkout = 1
            ''', (date,))
            early_employees = cursor.fetchall()
            
            return {
                'date': date,
                'total_employees': total_employees,
                'checked_in': checked_in_count,
                'checked_out': checked_out_count,
                'late_checkins': late_count,
                'early_checkouts': early_checkout_count,
                'late_employees': late_employees,
                'early_employees': early_employees
            }
    
    def log_server_activity(self, activity_type, details=None):
        """Log server activity for monitoring"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO server_activity (activity_type, details)
                VALUES (?, ?)
            ''', (activity_type, details))
            conn.commit()
    
    def get_all_admins_for_daily_summary(self):
        """Get all admins who should receive daily summary"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT telegram_id FROM admins 
                WHERE receive_daily_summary = 1
            ''')
            return [row[0] for row in cursor.fetchall()]
    
    def log_notification(self, telegram_id, notification_type, message):
        """Log notification sent to database"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notification_log (telegram_id, notification_type, message)
                VALUES (?, ?, ?)
            ''', (telegram_id, notification_type, message))
            conn.commit()
    
    # Import all other methods from the original database class
    def register_employee(self, telegram_id, username=None, first_name=None, last_name=None, phone_number=None):
        """Register a new employee"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO employees 
                (telegram_id, username, first_name, last_name, phone_number)
                VALUES (?, ?, ?, ?, ?)
            ''', (telegram_id, username, first_name, last_name, phone_number))
            conn.commit()
    
    def is_employee_registered(self, telegram_id):
        """Check if employee is registered"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT telegram_id FROM employees WHERE telegram_id = ? AND is_active = 1', (telegram_id,))
            return cursor.fetchone() is not None
    
    def check_in(self, telegram_id, latitude, longitude, location_note=None):
        """Legacy check-in method for backward compatibility"""
        return self.check_in_with_reason(telegram_id, latitude, longitude)[:2]
    
    def check_out(self, telegram_id, latitude, longitude, location_note=None):
        """Legacy check-out method for backward compatibility"""
        return self.check_out_with_reason(telegram_id, latitude, longitude)[:2]
    
    def get_attendance_status(self, telegram_id):
        """Get current attendance status for today"""
        egypt_tz = pytz.timezone('Africa/Cairo')
        current_date = datetime.now(egypt_tz).date()
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT check_in_time, check_out_time, status 
                FROM attendance 
                WHERE telegram_id = ? AND date = ?
            ''', (telegram_id, current_date))
            
            return cursor.fetchone()
    
    def add_admin(self, telegram_id):
        """Add an admin"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO admins (telegram_id) VALUES (?)', (telegram_id,))
            conn.commit()
    
    def is_admin(self, telegram_id):
        """Check if user is admin"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT telegram_id FROM admins WHERE telegram_id = ?', (telegram_id,))
            return cursor.fetchone() is not None
    
    def get_admin_alert_settings(self, telegram_id):
        """Get admin alert settings"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT alert_enabled, late_threshold_minutes 
                FROM admins WHERE telegram_id = ?
            ''', (telegram_id,))
            result = cursor.fetchone()
            if result:
                return result[0], result[1]
            return True, 30  # Default settings
    
    def update_admin_alert_settings(self, telegram_id, alert_enabled=None, late_threshold=None):
        """Update admin alert settings"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            if alert_enabled is not None:
                cursor.execute('''
                    UPDATE admins SET alert_enabled = ? WHERE telegram_id = ?
                ''', (alert_enabled, telegram_id))
            if late_threshold is not None:
                cursor.execute('''
                    UPDATE admins SET late_threshold_minutes = ? WHERE telegram_id = ?
                ''', (late_threshold, telegram_id))
            conn.commit()
    
    def get_all_employees_report(self):
        """Get all employees report for today"""
        egypt_tz = pytz.timezone('Africa/Cairo')
        today = datetime.now(egypt_tz).date()
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.first_name, e.last_name, e.username, 
                       a.check_in_time, a.check_out_time, a.status
                FROM employees e
                LEFT JOIN attendance a ON e.telegram_id = a.telegram_id AND a.date = ?
                WHERE e.is_active = 1
                ORDER BY e.first_name
            ''', (today,))
            return cursor.fetchall() 