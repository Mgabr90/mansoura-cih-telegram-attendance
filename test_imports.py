#!/usr/bin/env python3
"""
Import Test Script for Mansoura CIH Telegram Attendance System
Tests all critical imports without requiring external dependencies
"""

import sys
import os
import ast

# Add src to path
sys.path.insert(0, 'src')

def test_config_imports():
    """Test config imports"""
    try:
        from config.settings import (
            BOT_TOKEN, OFFICE_LATITUDE, OFFICE_LONGITUDE, 
            OFFICE_RADIUS, TIMEZONE, validate_settings
        )
        print("✅ Config settings import successfully")
        return True
    except Exception as e:
        print(f"❌ Config import failed: {e}")
        return False

def test_database_import():
    """Test database module import (syntax only)"""
    try:
        with open('src/database.py', 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        print("✅ Database module syntax valid")
        return True
    except Exception as e:
        print(f"❌ Database syntax error: {e}")
        return False

def test_handlers_import():
    """Test handlers import (syntax only)"""
    try:
        # Test employee handlers
        with open('src/handlers/employee_handlers.py', 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        print("✅ Employee handlers syntax valid")
        
        # Test admin handlers  
        with open('src/handlers/admin_handlers.py', 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        print("✅ Admin handlers syntax valid")
        
        return True
    except Exception as e:
        print(f"❌ Handlers syntax error: {e}")
        return False

def test_utils_import():
    """Test utils import (syntax only)"""
    try:
        with open('src/utils/keyboards.py', 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        print("✅ Keyboards utils syntax valid")
        
        with open('src/utils/messages.py', 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        print("✅ Messages utils syntax valid")
        
        return True
    except Exception as e:
        print(f"❌ Utils syntax error: {e}")
        return False

def test_main_webhook():
    """Test main webhook syntax"""
    try:
        with open('src/main_webhook.py', 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        print("✅ Main webhook syntax valid")
        return True
    except Exception as e:
        print(f"❌ Main webhook syntax error: {e}")
        return False

def test_location_utils():
    """Test location utils"""
    try:
        with open('src/location_utils.py', 'r', encoding='utf-8') as f:
            ast.parse(f.read())
        print("✅ Location utils syntax valid")
        return True
    except Exception as e:
        print(f"❌ Location utils syntax error: {e}")
        return False

def main():
    """Run all import tests"""
    print("🧪 Testing Imports for Mansoura CIH Attendance System")
    print("=" * 55)
    
    tests = [
        test_config_imports,
        test_database_import, 
        test_handlers_import,
        test_utils_import,
        test_main_webhook,
        test_location_utils
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 55)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All import tests passed! Ready for deployment!")
        return 0
    else:
        print("💥 Some tests failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 