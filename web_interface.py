"""
El Mansoura CIH Attendance System - Web Interface
A modern web dashboard for attendance management and reporting
Compatible with the new modular architecture
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
import threading

# Import from new modular structure
from attendance_system.core.database import AttendanceDatabase
from attendance_system.core.config import Config

# Initialize Flask app
app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')
app.secret_key = os.environ.get('WEB_SECRET_KEY', 'mansoura-cih-attendance-secret-key-2024')

# Initialize database and config
config = Config()
db = AttendanceDatabase()

# Admin credentials
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
        total_employees = len(db.get_all_employees())
        today = datetime.now(pytz.timezone(config.TIMEZONE)).date()
        
        # Get today's attendance records
        today_records = [r for r in db.get_daily_attendance_records(today) if r['check_in_time']]
        today_checkins = len(today_records)
        
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
        egypt_tz = pytz.timezone(config.TIMEZONE)
        today = datetime.now(egypt_tz).date()
        
        # Get all employees and today's records
        all_employees = db.get_all_employees()
        today_records = db.get_daily_attendance_records(today)
        
        # Calculate stats
        total_employees = len(all_employees)
        today_checkins = len([r for r in today_records if r['check_in_time']])
        today_checkouts = len([r for r in today_records if r['check_out_time']])
        
        # Get currently checked in employees
        active_employees = len([r for r in today_records if r['check_in_time'] and not r['check_out_time']])
        
        # Calculate late employees (after 9:30 AM)
        late_threshold = datetime.combine(today, datetime.strptime("09:30", "%H:%M").time())
        late_threshold = egypt_tz.localize(late_threshold)
        late_employees = 0
        
        for record in today_records:
            if record['check_in_time']:
                check_in_dt = datetime.fromisoformat(record['check_in_time'].replace('Z', '+00:00'))
                if check_in_dt > late_threshold:
                    late_employees += 1
        
        stats = {
            'total_employees': total_employees,
            'today_checkins': today_checkins,
            'today_checkouts': today_checkouts,
            'late_employees': late_employees,
            'active_employees': active_employees,
            'attendance_rate': round((today_checkins / total_employees * 100) if total_employees > 0 else 0, 1)
        }
        
        # Get recent activity (last 10 records)
        recent_activity = today_records[-10:] if today_records else []
        
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
        settings_data = {
            'office_location': f"{config.OFFICE_LATITUDE}, {config.OFFICE_LONGITUDE}",
            'attendance_radius': f"{config.OFFICE_RADIUS}m",
            'timezone': config.TIMEZONE,
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
        egypt_tz = pytz.timezone(config.TIMEZONE)
        end_date = datetime.now(egypt_tz).date()
        start_date = end_date - timedelta(days=6)
        
        chart_data = []
        current_date = start_date
        
        while current_date <= end_date:
            records = db.get_daily_attendance_records(current_date)
            checkins = len([r for r in records if r['check_in_time']])
            checkouts = len([r for r in records if r['check_out_time']])
            
            chart_data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'checkins': checkins,
                'checkouts': checkouts
            })
            current_date += timedelta(days=1)
        
        return jsonify({
            'dates': [item['date'] for item in chart_data],
            'checkins': [item['checkins'] for item in chart_data],
            'checkouts': [item['checkouts'] for item in chart_data]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/export/<report_type>')
@login_required
def export_report(report_type):
    """Export reports as CSV"""
    try:
        egypt_tz = pytz.timezone(config.TIMEZONE)
        today = datetime.now(egypt_tz).date()
        
        if report_type == 'daily':
            date_str = request.args.get('date', today.strftime('%Y-%m-%d'))
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            data = db.get_daily_attendance_records(date_obj)
            filename = f'daily_report_{date_str}.csv'
            
        elif report_type == 'employees':
            data = db.get_all_employees()
            filename = 'employees_list.csv'
            
        else:
            return jsonify({'error': 'Invalid report type'}), 400
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Create CSV
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode()),
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
        current_status = db.is_admin(employee_id)
        
        if current_status:
            # Remove admin (if it's a method available)
            return jsonify({'error': 'Remove admin function not implemented'}), 501
        else:
            db.add_admin(employee_id)
            return jsonify({'success': True, 'message': 'Admin status granted'})
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats')
@login_required
def get_stats():
    """Get real-time stats"""
    try:
        egypt_tz = pytz.timezone(config.TIMEZONE)
        today = datetime.now(egypt_tz).date()
        
        all_employees = db.get_all_employees()
        today_records = db.get_daily_attendance_records(today)
        
        stats = {
            'total_employees': len(all_employees),
            'today_checkins': len([r for r in today_records if r['check_in_time']]),
            'today_checkouts': len([r for r in today_records if r['check_out_time']]),
            'active_employees': len([r for r in today_records if r['check_in_time'] and not r['check_out_time']])
        }
        
        stats['attendance_rate'] = round(
            (stats['today_checkins'] / stats['total_employees'] * 100) 
            if stats['total_employees'] > 0 else 0, 1
        )
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Health check endpoint for the web interface
@app.route('/web-health')
def web_health():
    """Web interface health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'web-interface',
        'timestamp': datetime.now(pytz.timezone(config.TIMEZONE)).isoformat()
    })

if __name__ == '__main__':
    print("🌐 Starting El Mansoura CIH Web Interface...")
    print(f"📍 Office Location: {config.OFFICE_LATITUDE}, {config.OFFICE_LONGITUDE}")
    print(f"🎯 Office Radius: {config.OFFICE_RADIUS}m")
    print("🔐 Admin Login: /login")
    print("=" * 50)
    
    # Run Flask app
    app.run(
        host='0.0.0.0', 
        port=int(os.environ.get('PORT', 5000)),
        debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    ) 