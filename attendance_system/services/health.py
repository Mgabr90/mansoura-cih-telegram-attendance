"""
Health service module for the Enhanced Attendance System.

This module provides health monitoring and server wake-up functionality.
"""

import asyncio
import logging
import threading
from datetime import datetime
from typing import Optional

from flask import Flask, jsonify

from ..core.database import AttendanceDatabase
from ..core.config import Config

logger = logging.getLogger(__name__)


class HealthService:
    """
    Health service class for server monitoring and wake-up functionality.
    
    Provides HTTP health endpoints and keeps the server active for platforms
    like Render free tier that sleep inactive services.
    """
    
    def __init__(self, db: AttendanceDatabase):
        """
        Initialize health service.
        
        Args:
            db: Database instance
        """
        self.db = db
        self.app = Flask(__name__)
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False
        
        # Setup Flask routes
        self._setup_routes()
        
        logger.info("Health service initialized")
    
    def _setup_routes(self) -> None:
        """Setup Flask routes for health endpoints."""
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            """Health check endpoint."""
            try:
                # Test database connection
                self.db.log_server_activity('health_check', 'Health endpoint accessed')
                
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                return jsonify({
                    'status': 'healthy',
                    'service': 'Enhanced Attendance System',
                    'timestamp': current_time,
                    'timezone': Config.TIMEZONE,
                    'database': 'connected'
                }), 200
                
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return jsonify({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }), 500
        
        @self.app.route('/status', methods=['GET'])
        def server_status():
            """Detailed server status endpoint."""
            try:
                # Get system statistics
                total_employees = len(self.db.get_all_employees())
                total_admins = len(self.db.get_all_admins())
                
                today_summary = self.db.get_daily_summary()
                
                recent_activities = self.db.get_recent_server_activity(5)
                
                status_data = {
                    'status': 'online',
                    'service': 'Enhanced Attendance System',
                    'version': '2.0.0',
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'timezone': Config.TIMEZONE,
                    'office_location': {
                        'latitude': Config.OFFICE_LATITUDE,
                        'longitude': Config.OFFICE_LONGITUDE,
                        'radius': Config.OFFICE_RADIUS,
                        'address': Config.OFFICE_ADDRESS
                    },
                    'statistics': {
                        'total_employees': total_employees,
                        'total_admins': total_admins,
                        'todays_attendance_rate': today_summary.get('attendance_rate', 0),
                        'todays_checkins': today_summary.get('checked_in', 0),
                        'todays_late_arrivals': today_summary.get('late_checkins', 0)
                    },
                    'features': {
                        'location_only_attendance': Config.LOCATION_ONLY_ATTENDANCE,
                        'manual_entry_disabled': Config.MANUAL_ENTRY_DISABLED,
                        'server_wakeup_enabled': Config.ENABLE_SERVER_WAKEUP,
                        'daily_summary_time': Config.ADMIN_DAILY_SUMMARY_TIME
                    },
                    'recent_activity': [
                        {
                            'timestamp': activity[0],
                            'type': activity[1],
                            'description': activity[2]
                        } for activity in recent_activities
                    ]
                }
                
                # Log status request
                self.db.log_server_activity('status_check', 'Status endpoint accessed')
                
                return jsonify(status_data), 200
                
            except Exception as e:
                logger.error(f"Status check failed: {e}")
                return jsonify({
                    'status': 'error',
                    'error': str(e),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }), 500
        
        @self.app.route('/ping', methods=['GET'])
        def ping():
            """Simple ping endpoint."""
            return jsonify({
                'message': 'pong',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }), 200
        
        @self.app.route('/stats', methods=['GET'])
        def attendance_stats():
            """Attendance statistics endpoint."""
            try:
                summary = self.db.get_daily_summary()
                
                stats = {
                    'date': summary.get('date', datetime.now().strftime('%Y-%m-%d')),
                    'total_employees': summary.get('total_employees', 0),
                    'checked_in_today': summary.get('checked_in', 0),
                    'checked_out_today': summary.get('checked_out', 0),
                    'attendance_rate': summary.get('attendance_rate', 0),
                    'late_checkins': summary.get('late_checkins', 0),
                    'early_checkouts': summary.get('early_checkouts', 0),
                    'currently_working': summary.get('checked_in', 0) - summary.get('checked_out', 0)
                }
                
                self.db.log_server_activity('stats_check', 'Stats endpoint accessed')
                
                return jsonify(stats), 200
                
            except Exception as e:
                logger.error(f"Stats check failed: {e}")
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }), 500
        
        @self.app.route('/activity', methods=['GET'])
        def recent_activity():
            """Recent activity endpoint."""
            try:
                activities = self.db.get_recent_server_activity(20)
                
                activity_data = [
                    {
                        'timestamp': activity[0],
                        'type': activity[1],
                        'description': activity[2]
                    } for activity in activities
                ]
                
                self.db.log_server_activity('activity_check', 'Activity endpoint accessed')
                
                return jsonify({
                    'activities': activity_data,
                    'count': len(activity_data),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }), 200
                
            except Exception as e:
                logger.error(f"Activity check failed: {e}")
                return jsonify({
                    'error': str(e),
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }), 500
        
        # Disable Flask logging to avoid cluttering the console
        logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    async def start(self) -> None:
        """Start the health service."""
        if self.is_running:
            logger.warning("Health service is already running")
            return
        
        self.is_running = True
        
        # Start Flask server in a separate thread
        self.server_thread = threading.Thread(
            target=self._run_flask_server,
            daemon=True
        )
        self.server_thread.start()
        
        # Log startup
        self.db.log_server_activity('health_service_start', 'Health service started')
        
        logger.info(f"Health service started on port {Config.PORT}")
    
    async def stop(self) -> None:
        """Stop the health service."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Log shutdown
        self.db.log_server_activity('health_service_stop', 'Health service stopped')
        
        logger.info("Health service stopped")
    
    def _run_flask_server(self) -> None:
        """Run Flask server in thread."""
        try:
            self.app.run(
                host='0.0.0.0',
                port=Config.PORT,
                debug=False,
                use_reloader=False,
                threaded=True
            )
        except Exception as e:
            logger.error(f"Error running Flask server: {e}")
    
    def get_health_status(self) -> dict:
        """
        Get current health status.
        
        Returns:
            dict: Health status information
        """
        try:
            # Test database connection
            total_employees = len(self.db.get_all_employees())
            
            return {
                'status': 'healthy',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'database_connected': True,
                'server_running': self.is_running,
                'total_employees': total_employees
            }
            
        except Exception as e:
            logger.error(f"Health status check failed: {e}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'database_connected': False,
                'server_running': self.is_running,
                'error': str(e)
            }
    
    def is_healthy(self) -> bool:
        """
        Check if service is healthy.
        
        Returns:
            bool: True if healthy, False otherwise
        """
        try:
            status = self.get_health_status()
            return status['status'] == 'healthy'
        except:
            return False


def start_health_server_thread(db: AttendanceDatabase) -> HealthService:
    """
    Convenience function to start health server in thread.
    
    Args:
        db: Database instance
        
    Returns:
        HealthService: The health service instance
    """
    health_service = HealthService(db)
    
    # Run in background thread
    def run_health_server():
        try:
            asyncio.run(health_service.start())
        except Exception as e:
            logger.error(f"Error in health server thread: {e}")
    
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    return health_service 