#!/usr/bin/env python3
"""
Mansoura CIH Telegram Attendance System - Unified Launcher
Runs both the Telegram bot and web interface together
"""

import sys
import os
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_telegram_bot():
    """Run the Telegram bot in a separate thread"""
    try:
        print("🤖 Starting Telegram Bot...")
        from attendance_system.main import AttendanceBot
        
        bot = AttendanceBot()
        print("✅ Telegram Bot initialized successfully")
        asyncio.run(bot.run())
        
    except Exception as e:
        print(f"❌ Error starting Telegram bot: {e}")
        logging.exception("Failed to start Telegram bot")

def run_web_interface():
    """Run the web interface in a separate thread"""
    try:
        print("🌐 Starting Web Interface...")
        from web_interface import app
        
        # Use different port to avoid conflict with health service
        web_port = int(os.environ.get('WEB_PORT', 8081))
        print(f"✅ Web Interface starting on port {web_port}")
        app.run(
            host='0.0.0.0',
            port=web_port,
            debug=False,  # Disable debug in production
            use_reloader=False  # Disable reloader to prevent threading issues
        )
        
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")
        logging.exception("Failed to start web interface")

def main():
    """Main launcher function"""
    try:
        print("🚀 Starting El Mansoura CIH Attendance System")
        print("=" * 60)
        print("📍 El Mansoura CIH - Complete System")
        print("🤖 Telegram Bot + 🌐 Web Interface")
        print("🔧 Clean Modular Architecture")
        print("=" * 60)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Create thread pool for running both services
        with ThreadPoolExecutor(max_workers=2) as executor:
            print("🔄 Starting services...")
            
            # Submit both tasks
            bot_future = executor.submit(run_telegram_bot)
            web_future = executor.submit(run_web_interface)
            
            print("✅ Both services started!")
            print("📱 Telegram Bot: Active")
            print("🌐 Web Interface: http://localhost:8081")
            print("🔐 Web Admin Login: /login")
            print("=" * 60)
            print("Press Ctrl+C to stop all services")
            
            # Wait for either service to complete (or fail)
            try:
                # Keep the main thread alive
                while True:
                    time.sleep(1)
                    
                    # Check if any service has failed
                    if bot_future.done():
                        exception = bot_future.exception()
                        if exception:
                            print(f"🚨 Telegram Bot failed: {exception}")
                            break
                    
                    if web_future.done():
                        exception = web_future.exception()
                        if exception:
                            print(f"🚨 Web Interface failed: {exception}")
                            break
                            
            except KeyboardInterrupt:
                print("\n⚠️  Shutdown initiated by user")
                
    except KeyboardInterrupt:
        print("\n⚠️  System stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        logging.exception("Failed to start system")
        sys.exit(1)

if __name__ == "__main__":
    main() 