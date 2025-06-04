"""
Additional database methods for the web interface
These extend the main AttendanceDatabase class with web-specific functionality
"""

import sqlite3
from datetime import datetime, timedelta
import pytz

def extend_database_for_web(db_instance):
    """Add web-specific methods to the database instance"""
    
    def get_total_employees_count(self):
        """Get total number of registered employees"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM employees")
        return cursor.fetchone()[0]
    
    def get_daily_checkins_count(self, date):
        """Get number of check-ins for a specific date"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM attendance 
            WHERE DATE(check_in_time) = ? AND action = 'check_in'
        """, (date,))
        return cursor.fetchone()[0]
    
    def get_daily_checkouts_count(self, date):
        """Get number of check-outs for a specific date"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM attendance 
            WHERE DATE(check_out_time) = ? AND action = 'check_out'
        """, (date,))
        return cursor.fetchone()[0]
    
    def get_currently_checked_in_count(self):
        """Get number of employees currently checked in"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM attendance 
            WHERE DATE(check_in_time) = DATE('now') 
            AND check_out_time IS NULL
        """)
        return cursor.fetchone()[0]
    
    def get_recent_attendance_activity(self, limit=10):
        """Get recent attendance activity for admin dashboard"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                e.first_name || ' ' || COALESCE(e.last_name, '') as full_name,
                e.username,
                CASE 
                    WHEN a.check_in_time IS NOT NULL AND a.check_out_time IS NULL THEN 'check_in'
                    WHEN a.check_out_time IS NOT NULL THEN 'check_out'
                END as action,
                COALESCE(a.check_out_time, a.check_in_time) as last_action_time,
                'Within Range' as location_status,
                a.status
            FROM attendance a
            JOIN employees e ON a.telegram_id = e.telegram_id
            ORDER BY COALESCE(a.check_out_time, a.check_in_time) DESC
            LIMIT ?
        """, (limit,))
        return cursor.fetchall()
    
    def get_all_employees(self):
        """Get all employees with admin status"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                e.telegram_id,
                e.first_name,
                e.last_name,
                e.username,
                e.phone_number,
                e.created_at,
                CASE WHEN a.telegram_id IS NOT NULL THEN 1 ELSE 0 END as is_admin
            FROM employees e
            LEFT JOIN admins a ON e.telegram_id = a.telegram_id
            ORDER BY e.first_name
        """)
        return cursor.fetchall()
    
    def get_attendance_chart_data(self, start_date, end_date):
        """Get attendance data for charts"""
        cursor = self.conn.cursor()
        
        # Generate all dates in range
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date.strftime('%Y-%m-%d'))
            current_date += timedelta(days=1)
        
        chart_data = []
        for date in dates:
            # Count check-ins for this date
            cursor.execute("""
                SELECT COUNT(*) FROM attendance 
                WHERE DATE(check_in_time) = ?
            """, (date,))
            checkins = cursor.fetchone()[0]
            
            # Count check-outs for this date
            cursor.execute("""
                SELECT COUNT(*) FROM attendance 
                WHERE DATE(check_out_time) = ?
            """, (date,))
            checkouts = cursor.fetchone()[0]
            
            chart_data.append((date, checkins, checkouts))
        
        return chart_data
    
    def get_daily_report(self, date):
        """Get daily attendance report data"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                e.first_name || ' ' || COALESCE(e.last_name, '') as full_name,
                e.username,
                a.check_in_time,
                a.check_out_time,
                a.status,
                CASE 
                    WHEN a.check_in_time IS NOT NULL AND a.check_out_time IS NOT NULL 
                    THEN ROUND((JULIANDAY(a.check_out_time) - JULIANDAY(a.check_in_time)) * 24, 2)
                    ELSE 0 
                END as hours_worked
            FROM employees e
            LEFT JOIN attendance a ON e.telegram_id = a.telegram_id 
                AND DATE(a.check_in_time) = ?
            ORDER BY e.first_name
        """, (date,))
        return cursor.fetchall()
    
    def get_weekly_report(self, start_date, end_date):
        """Get weekly attendance report data"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                e.first_name || ' ' || COALESCE(e.last_name, '') as full_name,
                e.username,
                COUNT(a.check_in_time) as days_present,
                AVG(CASE 
                    WHEN a.check_in_time IS NOT NULL AND a.check_out_time IS NOT NULL 
                    THEN ROUND((JULIANDAY(a.check_out_time) - JULIANDAY(a.check_in_time)) * 24, 2)
                    ELSE 0 
                END) as avg_hours
            FROM employees e
            LEFT JOIN attendance a ON e.telegram_id = a.telegram_id 
                AND DATE(a.check_in_time) BETWEEN ? AND ?
            GROUP BY e.telegram_id, e.first_name, e.last_name, e.username
            ORDER BY e.first_name
        """, (start_date, end_date))
        return cursor.fetchall()
    
    def get_monthly_report(self, month):
        """Get monthly attendance report data"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                e.first_name || ' ' || COALESCE(e.last_name, '') as full_name,
                e.username,
                COUNT(a.check_in_time) as days_present,
                SUM(CASE 
                    WHEN a.check_in_time IS NOT NULL AND a.check_out_time IS NOT NULL 
                    THEN ROUND((JULIANDAY(a.check_out_time) - JULIANDAY(a.check_in_time)) * 24, 2)
                    ELSE 0 
                END) as total_hours
            FROM employees e
            LEFT JOIN attendance a ON e.telegram_id = a.telegram_id 
                AND strftime('%Y-%m', a.check_in_time) = ?
            GROUP BY e.telegram_id, e.first_name, e.last_name, e.username
            ORDER BY e.first_name
        """, (month,))
        return cursor.fetchall()
    
    def remove_admin(self, telegram_id):
        """Remove admin privileges from a user"""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM admins WHERE telegram_id = ?", (telegram_id,))
        self.conn.commit()
        return cursor.rowcount > 0
    
    # Bind methods to the instance
    import types
    db_instance.get_total_employees_count = types.MethodType(get_total_employees_count, db_instance)
    db_instance.get_daily_checkins_count = types.MethodType(get_daily_checkins_count, db_instance)
    db_instance.get_daily_checkouts_count = types.MethodType(get_daily_checkouts_count, db_instance)
    db_instance.get_currently_checked_in_count = types.MethodType(get_currently_checked_in_count, db_instance)
    db_instance.get_recent_attendance_activity = types.MethodType(get_recent_attendance_activity, db_instance)
    db_instance.get_all_employees = types.MethodType(get_all_employees, db_instance)
    db_instance.get_attendance_chart_data = types.MethodType(get_attendance_chart_data, db_instance)
    db_instance.get_daily_report = types.MethodType(get_daily_report, db_instance)
    db_instance.get_weekly_report = types.MethodType(get_weekly_report, db_instance)
    db_instance.get_monthly_report = types.MethodType(get_monthly_report, db_instance)
    db_instance.remove_admin = types.MethodType(remove_admin, db_instance)
    
    return db_instance 