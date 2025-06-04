#!/usr/bin/env python3
"""
Production start script for Render deployment
Runs the El Mansoura CIH Attendance System optimized for cloud deployment
"""

import sys
import os
import logging

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        
        # Import after path setup
        from app import main as app_main
        
        print("✅ Starting unified application...")
        app_main()
        
    except Exception as e:
        print(f"❌ Error starting system: {e}")
        logging.exception("Failed to start system")
        sys.exit(1)

if __name__ == "__main__":
    main() 