#!/usr/bin/env python3
"""
Simple syntax validation script for the Telegram Attendance System
"""
import ast
import os
import sys

def test_file_syntax(filepath):
    """Test if a Python file has valid syntax"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        ast.parse(content)
        print(f"✅ {filepath}: Syntax OK")
        return True
    except SyntaxError as e:
        print(f"❌ {filepath}: Syntax Error - {e}")
        return False
    except Exception as e:
        print(f"⚠️  {filepath}: Error reading file - {e}")
        return False

def main():
    """Run syntax tests on all Python files"""
    print("🧪 Running Python Syntax Tests")
    print("=" * 40)
    
    # Test main files
    test_files = [
        'src/main_bot.py',
        'src/main.py',
        'src/config.py',
        'src/bot.py',
        'src/database.py',
        'src/notification_service.py',
        'src/location_utils.py'
    ]
    
    all_passed = True
    
    for filepath in test_files:
        if os.path.exists(filepath):
            if not test_file_syntax(filepath):
                all_passed = False
        else:
            print(f"⚠️  {filepath}: File not found")
    
    # Test service files
    service_files = []
    if os.path.exists('src/services'):
        for filename in os.listdir('src/services'):
            if filename.endswith('.py'):
                service_files.append(f'src/services/{filename}')
    
    # Test handler files
    handler_files = []
    if os.path.exists('src/handlers'):
        for filename in os.listdir('src/handlers'):
            if filename.endswith('.py'):
                handler_files.append(f'src/handlers/{filename}')
    
    # Test utility files
    util_files = []
    if os.path.exists('src/utils'):
        for filename in os.listdir('src/utils'):
            if filename.endswith('.py'):
                util_files.append(f'src/utils/{filename}')
    
    for filepath in service_files + handler_files + util_files:
        if not test_file_syntax(filepath):
            all_passed = False
    
    print("=" * 40)
    if all_passed:
        print("🎉 All syntax tests passed!")
        return 0
    else:
        print("💥 Some syntax tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 