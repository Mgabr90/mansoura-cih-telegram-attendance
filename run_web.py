#!/usr/bin/env python3
"""
Mansoura CIH Telegram Attendance System - Web Interface Only
Launcher for web interface only
"""

import sys
import os
import logging

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main launcher function for web interface only"""
    try:
        print("🌐 Starting Web Interface Only...")
        print("=" * 50)
        print("📍 El Mansoura CIH - Web Dashboard")
        print("🔧 Clean Modular Architecture")
        print("=" * 50)
        
        # Import and start the web interface
        from web_interface import app
        
        print("✅ Modules loaded successfully")
        print("🌐 Initializing Web Interface...")
        
        port = int(os.environ.get('PORT', 5000))
        print(f"🎯 Web Interface starting on port {port}")
        print(f"🔗 Access at: http://localhost:{port}")
        print("🔐 Admin Login: /login")
        
        # Run Flask app
        app.run(
            host='0.0.0.0',
            port=port,
            debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        )
        
    except KeyboardInterrupt:
        print("\n⚠️  Web interface stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")
        logging.exception("Failed to start web interface")
        sys.exit(1)

if __name__ == "__main__":
    main() 