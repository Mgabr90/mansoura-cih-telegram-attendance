#!/usr/bin/env python3
"""
Production start script for Render deployment
Runs the El Mansoura CIH Attendance System with full web interface and webhook integration
"""

import sys
import os
import logging
import threading
import time
from flask import Flask, request, jsonify
import asyncio
from telegram import Update

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_production_app():
    """Create the production Flask app with full web interface and webhook integration"""
    
    # Import and initialize the full web interface
    from web_interface import app as web_app
    
    # Use the existing web interface Flask app
    app = web_app
    
    # Initialize bot instance
    bot_instance = None
    
    def initialize_bot():
        """Initialize the bot in webhook mode"""
        nonlocal bot_instance
        try:
            from attendance_system.main import AttendanceBot
            bot_instance = AttendanceBot()
            
            # Initialize the application but don't start polling
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(bot_instance.app.initialize())
            loop.run_until_complete(bot_instance.app.start())
            
            # Start notification service in background
            def start_notifications():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(bot_instance.notification_service.run_scheduler())
            
            notification_thread = threading.Thread(target=start_notifications, daemon=True)
            notification_thread.start()
            
            print("✅ Bot initialized in webhook mode")
            return True
        except Exception as e:
            print(f"❌ Bot initialization error: {e}")
            logging.exception("Bot initialization failed")
            return False
    
    @app.route('/webhook', methods=['POST'])
    def webhook():
        """Handle incoming Telegram webhooks"""
        try:
            if not bot_instance:
                return jsonify({'error': 'Bot not initialized'}), 500
            
            # Get update from Telegram
            update_dict = request.get_json()
            if not update_dict:
                return jsonify({'error': 'No data received'}), 400
            
            # Process update asynchronously
            update = Update.de_json(update_dict, bot_instance.app.bot)
            
            # Run the update processing in a new event loop
            def process_update():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(bot_instance.app.process_update(update))
                except Exception as e:
                    logging.error(f"Error processing update: {e}")
                finally:
                    loop.close()
            
            # Process in background thread to avoid blocking
            threading.Thread(target=process_update, daemon=True).start()
            
            return jsonify({'status': 'ok'}), 200
            
        except Exception as e:
            logging.error(f"Webhook error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    @app.route('/set-webhook', methods=['POST'])
    def set_webhook():
        """Set the webhook URL for the bot"""
        try:
            if not bot_instance:
                return jsonify({'error': 'Bot not initialized'}), 500
            
            webhook_url = os.environ.get('WEBHOOK_URL')
            if not webhook_url:
                # Auto-generate webhook URL from Render
                webhook_url = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/webhook"
            
            # Set webhook asynchronously
            def set_webhook_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        bot_instance.app.bot.set_webhook(url=webhook_url)
                    )
                    print(f"✅ Webhook set to: {webhook_url}")
                    return result
                except Exception as e:
                    print(f"❌ Webhook setup error: {e}")
                    return False
                finally:
                    loop.close()
            
            result = set_webhook_async()
            
            return jsonify({
                'status': 'success' if result else 'error',
                'webhook_url': webhook_url,
                'message': 'Webhook set successfully' if result else 'Failed to set webhook'
            }), 200 if result else 500
            
        except Exception as e:
            logging.error(f"Set webhook error: {e}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/system-info')
    def system_info():
        """System information endpoint"""
        bot_status = 'running' if bot_instance else 'initializing'
        return jsonify({
            'message': 'El Mansoura CIH Telegram Attendance System - Full Production',
            'status': 'running',
            'bot': 'webhook-mode',
            'bot_status': bot_status,
            'webhook_ready': bot_instance is not None,
            'web_interface': 'active',
            'endpoints': {
                'webhook': '/webhook',
                'web_health': '/web-health',
                'admin_login': '/login',
                'admin_dashboard': '/admin',
                'api_employees': '/api/employees',
                'api_attendance': '/api/attendance',
                'api_stats': '/api/stats'
            }
        }), 200
    
    # Initialize bot when app starts
    if initialize_bot():
        print("🤖 Bot ready for webhook mode")
    
    return app

def main():
    """Main production launcher"""
    try:
        print("🚀 Starting El Mansoura CIH Attendance System (Full Production)")
        print("=" * 60)
        
        # Setup logging for production
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Get port from environment
        port = int(os.environ.get('PORT', 10000))
        
        # Create Flask app with full web interface
        app = create_production_app()
        
        print(f"🏥 Starting full system on port {port}")
        print("🌐 Full Web Interface: Active")
        print("🔗 Webhook endpoint: /webhook")
        print("🔐 Admin login: /login")
        print("📊 Admin dashboard: /admin")
        print("🏥 Health check: /web-health")
        print("📋 System info: /system-info")
        
        # Run Flask app
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        logging.exception("Failed to start system")
        sys.exit(1)

if __name__ == "__main__":
    main() 