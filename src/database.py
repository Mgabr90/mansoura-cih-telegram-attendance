import sqlite3
import os
from datetime import datetime, timedelta
import pytz
import csv
import io

class AttendanceDatabase:
    def __init__(self, db_name='attendance.db'):
        self.db_name = db_name
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Employees table
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Attendance records table
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
                    date DATE,
                    status TEXT DEFAULT 'checked_in',
                    FOREIGN KEY (telegram_id) REFERENCES employees (telegram_id)
                )
            ''')
            
            # Add location note columns if they don't exist (for existing databases)
            try:
                cursor.execute('ALTER TABLE attendance ADD COLUMN check_in_location_note TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute('ALTER TABLE attendance ADD COLUMN check_out_location_note TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Admins table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admins (
                    telegram_id INTEGER PRIMARY KEY,
                    alert_enabled BOOLEAN DEFAULT 1,
                    late_threshold_minutes INTEGER DEFAULT 30,
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
            
            conn.commit()
    
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
        """Record check-in time and location with optional location note"""
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
            
            cursor.execute('''
                INSERT INTO attendance 
                (telegram_id, check_in_time, check_in_latitude, check_in_longitude, check_in_location_note, date, status)
                VALUES (?, ?, ?, ?, ?, ?, 'checked_in')
            ''', (telegram_id, current_time, latitude, longitude, location_note, current_date))
            conn.commit()
            return True, f"Check-in successful at {current_time.strftime('%H:%M:%S')}"
    
    def check_out(self, telegram_id, latitude, longitude, location_note=None):
        """Record check-out time and location with optional location note"""
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
            
            cursor.execute('''
                UPDATE attendance 
                SET check_out_time = ?, check_out_latitude = ?, check_out_longitude = ?, check_out_location_note = ?, status = 'checked_out'
                WHERE id = ?
            ''', (current_time, latitude, longitude, location_note, record[0]))
            conn.commit()
            return True, f"Check-out successful at {current_time.strftime('%H:%M:%S')}"
    
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
    
    def get_employee_attendance_report(self, telegram_id, days=7):
        """Get attendance report for an employee"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, check_in_time, check_out_time, status
                FROM attendance 
                WHERE telegram_id = ?
                ORDER BY date DESC
                LIMIT ?
            ''', (telegram_id, days))
            
            return cursor.fetchall()
    
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
    
    def get_all_employees_report(self, date=None):
        """Get attendance report for all employees"""
        egypt_tz = pytz.timezone('Africa/Cairo')
        if date is None:
            date = datetime.now(egypt_tz).date()
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.first_name, e.last_name, e.username,
                       a.check_in_time, a.check_out_time, a.status
                FROM employees e
                LEFT JOIN attendance a ON e.telegram_id = a.telegram_id AND a.date = ?
                WHERE e.is_active = 1
                ORDER BY e.first_name
            ''', (date,))
            
            return cursor.fetchall()
    
    def export_attendance_csv(self, start_date=None, end_date=None):
        """Export attendance data to CSV format"""
        egypt_tz = pytz.timezone('Africa/Cairo')
        
        if end_date is None:
            end_date = datetime.now(egypt_tz).date()
        if start_date is None:
            start_date = end_date - timedelta(days=30)  # Default last 30 days
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    e.first_name || ' ' || COALESCE(e.last_name, '') as full_name,
                    e.username,
                    e.phone_number,
                    a.date,
                    a.check_in_time,
                    a.check_out_time,
                    CASE 
                        WHEN a.check_in_time IS NOT NULL AND a.check_out_time IS NOT NULL 
                        THEN ROUND((julianday(a.check_out_time) - julianday(a.check_in_time)) * 24, 2)
                        ELSE NULL 
                    END as work_hours,
                    a.status,
                    a.check_in_latitude,
                    a.check_in_longitude,
                    a.check_out_latitude,
                    a.check_out_longitude
                FROM employees e
                LEFT JOIN attendance a ON e.telegram_id = a.telegram_id 
                WHERE e.is_active = 1 
                AND (a.date BETWEEN ? AND ? OR a.date IS NULL)
                ORDER BY a.date DESC, e.first_name
            ''', (start_date, end_date))
            
            return cursor.fetchall()
    
    def get_employee_list_csv(self):
        """Export employee list to CSV format"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    telegram_id,
                    first_name || ' ' || COALESCE(last_name, '') as full_name,
                    username,
                    phone_number,
                    created_at,
                    CASE WHEN is_active = 1 THEN 'Active' ELSE 'Inactive' END as status
                FROM employees
                ORDER BY first_name
            ''')
            
            return cursor.fetchall()
    
    def get_daily_summary_csv(self, date=None):
        """Get daily attendance summary in CSV format"""
        egypt_tz = pytz.timezone('Africa/Cairo')
        if date is None:
            date = datetime.now(egypt_tz).date()
            
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    e.first_name || ' ' || COALESCE(e.last_name, '') as full_name,
                    e.username,
                    CASE 
                        WHEN a.check_in_time IS NOT NULL 
                        THEN strftime('%H:%M', a.check_in_time)
                        ELSE 'Absent'
                    END as check_in,
                    CASE 
                        WHEN a.check_out_time IS NOT NULL 
                        THEN strftime('%H:%M', a.check_out_time)
                        ELSE CASE 
                            WHEN a.check_in_time IS NOT NULL THEN 'Still Working'
                            ELSE 'Absent'
                        END
                    END as check_out,
                    CASE 
                        WHEN a.check_in_time IS NOT NULL AND a.check_out_time IS NOT NULL 
                        THEN ROUND((julianday(a.check_out_time) - julianday(a.check_in_time)) * 24, 2)
                        ELSE NULL 
                    END as work_hours,
                    COALESCE(a.status, 'Absent') as status
                FROM employees e
                LEFT JOIN attendance a ON e.telegram_id = a.telegram_id AND a.date = ?
                WHERE e.is_active = 1
                ORDER BY e.first_name
            ''', (date,))
            
            return cursor.fetchall()
    
    def get_monthly_report_csv(self, year=None, month=None):
        """Get monthly attendance report in CSV format"""
        egypt_tz = pytz.timezone('Africa/Cairo')
        now = datetime.now(egypt_tz)
        
        if year is None:
            year = now.year
        if month is None:
            month = now.month
            
        # Get start and end dates for the month
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
            
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    e.first_name || ' ' || COALESCE(e.last_name, '') as full_name,
                    e.username,
                    COUNT(a.date) as days_present,
                    ROUND(AVG(
                        CASE 
                            WHEN a.check_in_time IS NOT NULL AND a.check_out_time IS NOT NULL 
                            THEN (julianday(a.check_out_time) - julianday(a.check_in_time)) * 24
                            ELSE NULL 
                        END
                    ), 2) as avg_work_hours,
                    ROUND(SUM(
                        CASE 
                            WHEN a.check_in_time IS NOT NULL AND a.check_out_time IS NOT NULL 
                            THEN (julianday(a.check_out_time) - julianday(a.check_in_time)) * 24
                            ELSE 0 
                        END
                    ), 2) as total_work_hours
                FROM employees e
                LEFT JOIN attendance a ON e.telegram_id = a.telegram_id 
                WHERE e.is_active = 1 
                AND (a.date BETWEEN ? AND ? OR a.date IS NULL)
                GROUP BY e.telegram_id, e.first_name, e.last_name, e.username
                ORDER BY e.first_name
            ''', (start_date, end_date))
            
            return cursor.fetchall()
    
    def create_csv_string(self, data, headers):
        """Convert data to CSV string"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(data)
        return output.getvalue()

    def update_reminder_settings(self, telegram_id, reminder_enabled=None, reminder_time=None, 
                                checkout_reminder_enabled=None, checkout_reminder_time=None):
        """Update employee reminder settings"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            update_parts = []
            params = []
            
            if reminder_enabled is not None:
                update_parts.append("reminder_enabled = ?")
                params.append(reminder_enabled)
            
            if reminder_time is not None:
                update_parts.append("reminder_time = ?")
                params.append(reminder_time)
                
            if checkout_reminder_enabled is not None:
                update_parts.append("checkout_reminder_enabled = ?")
                params.append(checkout_reminder_enabled)
                
            if checkout_reminder_time is not None:
                update_parts.append("checkout_reminder_time = ?")
                params.append(checkout_reminder_time)
            
            if update_parts:
                params.append(telegram_id)
                query = f"UPDATE employees SET {', '.join(update_parts)} WHERE telegram_id = ?"
                cursor.execute(query, params)
                conn.commit()

    def get_employees_for_checkin_reminder(self, current_time):
        """Get employees who need check-in reminders"""
        egypt_tz = pytz.timezone('Africa/Cairo')
        today = datetime.now(egypt_tz).date()
        current_time_str = current_time.strftime('%H:%M')
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.telegram_id, e.first_name, e.reminder_time
                FROM employees e
                LEFT JOIN attendance a ON e.telegram_id = a.telegram_id AND a.date = ?
                WHERE e.is_active = 1 
                AND e.reminder_enabled = 1
                AND e.reminder_time = ?
                AND a.telegram_id IS NULL
            ''', (today, current_time_str))
            
            return cursor.fetchall()

    def get_employees_for_checkout_reminder(self, current_time):
        """Get employees who need check-out reminders"""
        egypt_tz = pytz.timezone('Africa/Cairo')
        today = datetime.now(egypt_tz).date()
        current_time_str = current_time.strftime('%H:%M')
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.telegram_id, e.first_name, e.checkout_reminder_time
                FROM employees e
                JOIN attendance a ON e.telegram_id = a.telegram_id AND a.date = ?
                WHERE e.is_active = 1 
                AND e.checkout_reminder_enabled = 1
                AND e.checkout_reminder_time = ?
                AND a.check_out_time IS NULL
                AND a.check_in_time IS NOT NULL
            ''', (today, current_time_str))
            
            return cursor.fetchall()

    def get_late_employees(self, late_threshold_minutes=30):
        """Get employees who are late for check-in"""
        egypt_tz = pytz.timezone('Africa/Cairo')
        today = datetime.now(egypt_tz).date()
        current_time = datetime.now(egypt_tz).time()
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.telegram_id, e.first_name, e.last_name, e.username, e.reminder_time
                FROM employees e
                LEFT JOIN attendance a ON e.telegram_id = a.telegram_id AND a.date = ?
                WHERE e.is_active = 1 
                AND a.telegram_id IS NULL
                AND time(e.reminder_time, '+' || ? || ' minutes') <= time(?)
            ''', (today, late_threshold_minutes, current_time.strftime('%H:%M')))
            
            return cursor.fetchall()

    def get_missed_checkout_employees(self, hours_threshold=10):
        """Get employees who forgot to check out"""
        egypt_tz = pytz.timezone('Africa/Cairo')
        today = datetime.now(egypt_tz).date()
        threshold_time = datetime.now(egypt_tz) - timedelta(hours=hours_threshold)
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.telegram_id, e.first_name, e.last_name, e.username, a.check_in_time
                FROM employees e
                JOIN attendance a ON e.telegram_id = a.telegram_id AND a.date = ?
                WHERE e.is_active = 1 
                AND a.check_out_time IS NULL
                AND a.check_in_time IS NOT NULL
                AND a.check_in_time <= ?
            ''', (today, threshold_time))
            
            return cursor.fetchall()

    def log_notification(self, telegram_id, notification_type, message):
        """Log sent notifications"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO notification_log (telegram_id, notification_type, message)
                VALUES (?, ?, ?)
            ''', (telegram_id, notification_type, message))
            conn.commit()

    def get_admin_alert_settings(self, telegram_id):
        """Get admin alert settings"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT alert_enabled, late_threshold_minutes
                FROM admins 
                WHERE telegram_id = ?
            ''', (telegram_id,))
            
            result = cursor.fetchone()
            return result if result else (True, 30)  # Default: enabled, 30 min threshold

    def update_admin_alert_settings(self, telegram_id, alert_enabled=None, late_threshold_minutes=None):
        """Update admin alert settings"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Get current settings
            current = self.get_admin_alert_settings(telegram_id)
            
            if alert_enabled is None:
                alert_enabled = current[0]
            if late_threshold_minutes is None:
                late_threshold_minutes = current[1]
            
            cursor.execute('''
                UPDATE admins 
                SET alert_enabled = ?, late_threshold_minutes = ?
                WHERE telegram_id = ?
            ''', (alert_enabled, late_threshold_minutes, telegram_id))
            conn.commit()

    def get_all_admins_for_alerts(self):
        """Get all admins who have alerts enabled"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT telegram_id, late_threshold_minutes
                FROM admins 
                WHERE alert_enabled = 1
            ''')
            
            return cursor.fetchall() 