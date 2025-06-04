#!/usr/bin/env python3
"""
Launcher script for the Enhanced Mansoura CIH Telegram Attendance System.

This script provides a simple entry point to run the attendance bot
with proper error handling and environment setup.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the bot
try:
    from attendance_system.main import run_bot
    
    if __name__ == '__main__':
        print("🚀 Starting Enhanced Attendance System...")
        print("📍 Office: 29R3+7Q El Mansoura 1")
        print("🔒 Security: Location-only attendance")
        print("=" * 50)
        
        run_bot()
        
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Please ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting bot: {e}")
    sys.exit(1) 