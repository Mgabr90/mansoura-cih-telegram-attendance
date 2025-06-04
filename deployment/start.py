#!/usr/bin/env python3
"""
Production start script for Render deployment
Runs the El Mansoura CIH Attendance System optimized for cloud deployment
"""

import sys
import os
import logging
import threading
import time
from flask import Flask

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_health_app():
    """Create a simple Flask app for health checks"""
    app = Flask(__name__)
    
    @app.route('/web-health')
    def health_check():
        return {
            'status': 'healthy',
            'service': 'mansoura-cih-attendance',
            'bot_status': 'running'
        }, 200
    
    @app.route('/')
    def index():
        return {
            'message': 'El Mansoura CIH Telegram Attendance System',
            'status': 'running',
            'bot': 'active'
        }, 200
    
    return app

def run_health_server():
    """Run the health check server"""
    try:
        port = int(os.environ.get('PORT', 10000))
        app = create_health_app()
        print(f"🏥 Health server starting on port {port}")
        app.run(host='0.0.0.0', port=port, debug=False)
    except Exception as e:
        print(f"❌ Health server error: {e}")
        logging.exception("Health server failed")

def run_telegram_bot():
    """Run the Telegram bot"""
    try:
        print("🤖 Starting Telegram Bot...")
        from attendance_system.main import AttendanceBot
        
        bot = AttendanceBot()
        print("✅ Telegram Bot initialized successfully")
        import asyncio
        asyncio.run(bot.run())
        
    except Exception as e:
        print(f"❌ Error starting Telegram bot: {e}")
        logging.exception("Failed to start Telegram bot")

def main():
    """Main production launcher"""
    try:
        print("🚀 Starting El Mansoura CIH Attendance System (Production)")
        print("=" * 60)
        
        # Setup logging for production
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Start health server in background thread
        health_thread = threading.Thread(target=run_health_server, daemon=True)
        health_thread.start()
        
        # Give health server time to start
        time.sleep(2)
        
        print("✅ Health server started")
        print("🤖 Starting Telegram bot...")
        
        # Run bot in main thread
        run_telegram_bot()
        
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        logging.exception("Failed to start system")
        sys.exit(1)

if __name__ == "__main__":
    main() 