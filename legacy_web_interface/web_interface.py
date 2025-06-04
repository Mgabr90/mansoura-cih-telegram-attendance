"""
El Mansoura CIH Attendance System - Web Interface
A modern web dashboard for attendance management and reporting
"""

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import pandas as pd
import io
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import pytz
import os
from functools import wraps
import json

# Import our database class
import sys
sys.path.append('src')
from database import AttendanceDatabase
from database_extensions import extend_database_for_web

app = Flask(__name__)
app.secret_key = os.environ.get('WEB_SECRET_KEY', 'mansoura-cih-attendance-secret-key-2024')

# Initialize database with extensions
db = AttendanceDatabase()
extend_database_for_web(db)

# Admin credentials (you can change these)
ADMIN_USERNAME = os.environ.get('WEB_ADMIN_USER', 'admin')
ADMIN_PASSWORD = os.environ.get('WEB_ADMIN_PASS', 'mansoura2024')

def login_required(f):
    """Decorator to require login for admin routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Home page with dashboard overview"""
    try:
        # Get basic stats
        total_employees = db.get_total_employees_count()
        today = datetime.now(pytz.timezone('Africa/Cairo')).date()
        today_checkins = db.get_daily_checkins_count(today)
        
        stats = {
            'total_employees': total_employees,
            'today_checkins': today_checkins,
            'attendance_rate': round((today_checkins / total_employees * 100) if total_employees > 0 else 0, 1)
        }
        
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Admin login page"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            session['username'] = username
            flash('Successfully logged in!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout route"""
    session.clear()
    flash('Successfully logged out!', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard with detailed analytics"""
    try:
        egypt_tz = pytz.timezone('Africa/Cairo')
        today = datetime.now(egypt_tz).date()
        
        # Get comprehensive stats
        stats = {
            'total_employees': db.get_total_employees_count(),
            'today_checkins': db.get_daily_checkins_count(today),
            'today_checkouts': db.get_daily_checkouts_count(today),
            'late_employees': len(db.get_late_employees(30)),  # 30 min threshold
            'active_employees': db.get_currently_checked_in_count(),
        }
        
        # Calculate attendance rate
        stats['attendance_rate'] = round(
            (stats['today_checkins'] / stats['total_employees'] * 100) 
            if stats['total_employees'] > 0 else 0, 1
        )
        
        # Get recent activity
        recent_activity = db.get_recent_attendance_activity(10)
        
        return render_template('admin_dashboard.html', stats=stats, recent_activity=recent_activity)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/reports')
@login_required
def reports():
    """Reports page"""
    return render_template('reports.html')

@app.route('/employees')
@login_required
def employees():
    """Employee management page"""
    try:
        employees_data = db.get_all_employees()
        return render_template('employees.html', employees=employees_data)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/settings')
@login_required
def settings():
    """Settings management page"""
    try:
        # Get current settings from config
        settings_data = {
            'office_location': f"{os.environ.get('OFFICE_LATITUDE', '31.0364')}, {os.environ.get('OFFICE_LONGITUDE', '31.3789')}",
            'attendance_radius': os.environ.get('OFFICE_RADIUS', '100'),
            'timezone': os.environ.get('TIMEZONE', 'Africa/Cairo'),
            'working_hours': '09:00 - 17:00'
        }
        return render_template('settings.html', settings=settings_data)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/api/attendance-chart')
@login_required
def attendance_chart():
    """Generate attendance chart data"""
    try:
        # Get last 7 days data
        end_date = datetime.now(pytz.timezone('Africa/Cairo')).date()
        start_date = end_date - timedelta(days=6)
        
        chart_data = db.get_attendance_chart_data(start_date, end_date)
        
        return jsonify({
            'dates': [item[0] for item in chart_data],
            'checkins': [item[1] for item in chart_data],
            'checkouts': [item[2] for item in chart_data]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/<report_type>')
@login_required
def export_report(report_type):
    """Export reports as CSV"""
    try:
        egypt_tz = pytz.timezone('Africa/Cairo')
        today = datetime.now(egypt_tz).date()
        
        if report_type == 'daily':
            date_str = request.args.get('date', today.strftime('%Y-%m-%d'))
            data = db.get_daily_report(date_str)
            filename = f'daily_report_{date_str}.csv'
            
        elif report_type == 'weekly':
            end_date = today
            start_date = today - timedelta(days=6)
            data = db.get_weekly_report(start_date, end_date)
            filename = f'weekly_report_{start_date}_to_{end_date}.csv'
            
        elif report_type == 'monthly':
            month = request.args.get('month', today.strftime('%Y-%m'))
            data = db.get_monthly_report(month)
            filename = f'monthly_report_{month}.csv'
            
        elif report_type == 'employees':
            data = db.get_all_employees()
            filename = 'employees_list.csv'
            
        else:
            return jsonify({'error': 'Invalid report type'}), 400
        
        # Convert to DataFrame and CSV
        df = pd.DataFrame(data)
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/employees/<int:employee_id>/admin', methods=['POST'])
@login_required
def toggle_admin(employee_id):
    """Toggle admin status for an employee"""
    try:
        action = request.json.get('action')  # 'add' or 'remove'
        
        if action == 'add':
            db.add_admin(employee_id)
            return jsonify({'success': True, 'message': f'User {employee_id} added as admin'})
        elif action == 'remove':
            db.remove_admin(employee_id)
            return jsonify({'success': True, 'message': f'Admin privileges removed from user {employee_id}'})
        else:
            return jsonify({'error': 'Invalid action'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
@login_required
def get_stats():
    """Get real-time statistics"""
    try:
        egypt_tz = pytz.timezone('Africa/Cairo')
        today = datetime.now(egypt_tz).date()
        
        stats = {
            'total_employees': db.get_total_employees_count(),
            'today_checkins': db.get_daily_checkins_count(today),
            'today_checkouts': db.get_daily_checkouts_count(today),
            'active_employees': db.get_currently_checked_in_count(),
            'late_employees': len(db.get_late_employees(30))
        }
        
        stats['attendance_rate'] = round(
            (stats['today_checkins'] / stats['total_employees'] * 100) 
            if stats['total_employees'] > 0 else 0, 1
        )
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('DEBUG', 'False').lower() == 'true') 