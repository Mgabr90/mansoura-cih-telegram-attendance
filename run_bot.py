#!/usr/bin/env python3
"""
Mansoura CIH Telegram Attendance System - Bot Only
Launcher for Telegram bot only
"""

import sys
import os
import logging

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main launcher function for bot only"""
    try:
        print("🤖 Starting Telegram Bot Only...")
        print("=" * 50)
        print("📍 El Mansoura CIH - Telegram Bot")
        print("🔧 Clean Modular Architecture")
        print("=" * 50)
        
        # Import and start the bot
        from attendance_system.main import AttendanceBot
        
        print("✅ Modules loaded successfully")
        print("🤖 Initializing Telegram Bot...")
        
        # Create and run bot
        bot = AttendanceBot()
        print("🎯 Bot ready! Starting attendance tracking...")
        bot.run()
        
    except KeyboardInterrupt:
        print("\n⚠️  Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        logging.exception("Failed to start bot")
        sys.exit(1)

if __name__ == "__main__":
    main() 