from datetime import datetime
import pytz
from flask import Flask, jsonify
import os
import threading
import sqlite3

# Create a simple Flask app for health checks
health_app = Flask(__name__)

@health_app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint to keep server alive"""
    try:
        # Log the health check
        egypt_tz = pytz.timezone('Africa/Cairo')
        current_time = datetime.now(egypt_tz)
        
        # Simple database connection check
        db_name = os.getenv('DATABASE_NAME', 'attendance.db')
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Log this health check
        cursor.execute('''
            INSERT INTO server_activity (activity_type, details)
            VALUES (?, ?)
        ''', ('health_check', f'Health check at {current_time.strftime("%H:%M:%S")}'))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': current_time.isoformat(),
            'service': 'attendance_bot',
            'location': 'El Mansoura, Egypt'
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@health_app.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint"""
    return jsonify({'pong': True, 'timestamp': datetime.now().isoformat()}), 200

@health_app.route('/status', methods=['GET'])
def status():
    """Detailed status endpoint"""
    try:
        egypt_tz = pytz.timezone('Africa/Cairo')
        current_time = datetime.now(egypt_tz)
        
        db_name = os.getenv('DATABASE_NAME', 'attendance.db')
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Get basic stats
        cursor.execute('SELECT COUNT(*) FROM employees WHERE is_active = 1')
        active_employees = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM attendance WHERE date = ?', (current_time.date(),))
        today_checkins = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM admins')
        admin_count = cursor.fetchone()[0]
        
        # Get last activity
        cursor.execute('''
            SELECT activity_type, timestamp FROM server_activity
            ORDER BY timestamp DESC LIMIT 1
        ''')
        last_activity = cursor.fetchone()
        
        conn.close()
        
        return jsonify({
            'status': 'operational',
            'timestamp': current_time.isoformat(),
            'stats': {
                'active_employees': active_employees,
                'today_checkins': today_checkins,
                'admin_count': admin_count
            },
            'last_activity': {
                'type': last_activity[0] if last_activity else 'none',
                'time': last_activity[1] if last_activity else 'never'
            },
            'server_info': {
                'timezone': 'Africa/Cairo',
                'location': 'El Mansoura, Egypt'
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def run_health_server(port=8080):
    """Run the health check server in a separate thread"""
    health_app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def start_health_server_thread(port=8080):
    """Start health server in background thread"""
    health_thread = threading.Thread(target=run_health_server, args=(port,))
    health_thread.daemon = True
    health_thread.start()
    return health_thread 