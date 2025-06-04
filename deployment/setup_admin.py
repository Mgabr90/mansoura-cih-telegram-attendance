#!/usr/bin/env python3
"""
Setup script to add the first administrator to the attendance system.
Run this script once to set up the initial admin user.
"""

from attendance_system.core.database import AttendanceDatabase

def setup_first_admin():
    """Setup the first administrator"""
    print("🔧 El Mansoura Attendance Bot - Admin Setup")
    print("=" * 50)
    
    db = AttendanceDatabase()
    
    print("\nTo add the first admin, you need their Telegram User ID.")
    print("You can get the User ID by:")
    print("1. Having them send a message to your bot")
    print("2. Using @userinfobot on Telegram")
    print("3. Using @RawDataBot on Telegram")
    
    while True:
        try:
            user_input = input("\nEnter the Telegram User ID of the first admin: ").strip()
            
            if not user_input:
                print("❌ Please enter a valid User ID")
                continue
                
            admin_id = int(user_input)
            
            # Check if already admin
            if db.is_admin(admin_id):
                print(f"ℹ️  User {admin_id} is already an admin!")
                break
                
            # Add as admin
            db.add_admin(admin_id)
            print(f"✅ Successfully added User {admin_id} as admin!")
            print(f"🎉 They can now use admin commands like /admin and /add_admin")
            break
            
        except ValueError:
            print("❌ Invalid input. Please enter a numeric User ID.")
        except Exception as e:
            print(f"❌ Error: {e}")
            
    print("\n🚀 Admin setup complete! You can now start the bot with: python run.py")

if __name__ == "__main__":
    setup_first_admin() 