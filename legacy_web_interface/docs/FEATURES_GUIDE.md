# 📋 **El Mansoura Attendance Bot - Complete Features Guide**

## 🔐 **Data Export Access Control**

### **Who Can Export Data:**
- ✅ **Administrators ONLY** (users added via `/add_admin` command)
- ❌ **Regular employees CANNOT export data**

### **How Admins Can Export:**

#### **Method 1: Admin Panel (Recommended)**
1. Use `/admin` command
2. Click "📁 Export Data" button
3. Choose from quick export options:
   - 📊 Daily CSV (today's attendance)
   - 📈 Monthly CSV (current month summary)
   - 👥 Employee List CSV (all employees)
   - 📁 Full Attendance CSV (last 30 days)

#### **Method 2: Direct Commands**
```
/export_daily [YYYY-MM-DD]         # Daily report
/export_monthly [YYYY] [MM]        # Monthly summary  
/export_employees                  # Employee list
/export_attendance [start] [end]   # Detailed data
```

#### **Available Export Formats:**
- **Daily Summary**: Employee attendance for specific date
- **Monthly Report**: Attendance statistics and work hours
- **Employee List**: Complete employee database
- **Detailed Attendance**: Full data with GPS coordinates

---

## ⏰ **Employee Reminder System**

### **Reminder Features:**
- 🟢 **Check-in Reminders**: Automated notifications at set times
- 🔴 **Check-out Reminders**: End-of-day departure reminders
- 🎯 **Personalized Timing**: Each employee sets their own schedule
- 🔄 **Enable/Disable Control**: Full user control over notifications

### **How Employees Set Reminders:**

#### **Method 1: Interactive Menu**
```
/reminders
```
- Choose from reminder options
- Set check-in and check-out times
- View current settings
- Enable/disable notifications

#### **Method 2: Direct Commands**
```
/set_reminder checkin 09:00    # Set 9 AM check-in reminder
/set_reminder checkout 17:00   # Set 5 PM check-out reminder
```

### **Default Settings:**
- ✅ **Check-in reminder**: Enabled at 09:00
- ✅ **Check-out reminder**: Enabled at 17:00
- 🔄 **Auto-enabled** for new registrations

### **Reminder Examples:**
```
🔔 Check-in Reminder

Good morning Ahmed! 

⏰ It's 09:00 - time to check in to the office.
📍 Remember to be within 100m of El Mansoura office location.

Tap the button below to check in:
```

---

## 🚨 **Admin Alert System**

### **Alert Types:**
1. **🕐 Late Check-in Alerts**: Employees who haven't checked in after expected time
2. **⚠️ Missed Check-out Alerts**: Employees who forgot to check out
3. **📊 Real-time Monitoring**: Automatic detection and notification

### **How Admins Manage Alerts:**

#### **Configure Alert Settings:**
```
/admin_alerts
```
- ✅ Enable/disable alert notifications
- ⏱️ Set late check-in threshold (default: 30 minutes)
- 🧪 Test alert functionality

#### **Alert Schedule:**
- **Late Check-ins**: Every 30 minutes (9:00 AM - 12:00 PM)
- **Missed Check-outs**: Daily at 8:00 PM
- **Real-time Detection**: Continuous monitoring

### **Late Check-in Alert Example:**
```
🚨 Late Check-in Alert

3 employee(s) are late for check-in:

• Ahmed Hassan (@ahmed_h) - 45 minutes late
• Sara Mohamed (No username) - 20 minutes late
• Omar Ali (@omar_ali) - 35 minutes late

⏰ Threshold: 30 minutes
📅 Date: 2024-01-15
```

### **Missed Check-out Alert Example:**
```
⚠️ Missed Check-out Alert

2 employee(s) forgot to check out:

• Ahmed Hassan (@ahmed_h) - 10.5 hours since check-in
• Sara Mohamed (No username) - 11.2 hours since check-in

📅 Date: 2024-01-15
```

---

## 👑 **Admin Privileges**

### **How to Become Admin:**
1. **First Admin**: Use `python setup_admin.py` script
2. **Additional Admins**: Existing admin uses `/add_admin <user_id>`

### **Admin-Only Features:**
- 📊 View all employee reports
- 📁 Export attendance data in CSV format
- 🚨 Receive late/missed attendance alerts
- 👥 Manage employee data
- ⚙️ Configure system settings

### **Admin Commands:**
```
/admin                          # Admin control panel
/add_admin <user_id>           # Promote user to admin
/all_report                    # All employees report
/admin_alerts                  # Alert configuration
/export_daily [date]           # Export daily CSV
/export_monthly [year] [month] # Export monthly CSV
/export_employees              # Export employee list
/export_attendance [start] [end] # Export detailed data
```

---

## 🔔 **Notification Settings**

### **Employee Notification Controls:**
- ⏰ Set custom check-in reminder time
- 🔔 Set custom check-out reminder time
- 🔇 Disable all reminders
- 📊 View current reminder settings

### **Admin Alert Controls:**
- 🚨 Enable/disable late check-in alerts
- ⚠️ Enable/disable missed check-out alerts
- ⏱️ Customize late threshold (default: 30 minutes)
- 🧪 Test alert functionality

---

## 📊 **Data Privacy & Security**

### **Access Control:**
- 🔒 **Employee Data**: Only accessible by admins
- 🔐 **Export Functions**: Admin-only permissions
- 🛡️ **Personal Settings**: Employee-controlled reminders
- 📱 **Telegram Security**: User ID-based authentication

### **Data Export Includes:**
- 📍 GPS coordinates (for location verification)
- ⏰ Precise timestamps (Cairo timezone)
- 👤 Employee identification data
- 📊 Work duration calculations
- 📅 Attendance history and status

---

## 🚀 **Getting Started**

### **For Employees:**
1. `/start` - Register with contact sharing
2. `/reminders` - Set up notifications
3. Use location-based check-in/out buttons
4. `/status` and `/report` for personal tracking

### **For Administrators:**
1. Use setup script or get promoted by existing admin
2. `/admin_alerts` - Configure notification preferences
3. `/admin` - Access management dashboard
4. Use export commands for data analysis

### **System Requirements:**
- 📱 Telegram app with location services
- 📍 GPS enabled device
- 🏢 Physical presence within 100m of office
- 🌍 Cairo timezone (automatically handled)

---

## 💡 **Tips & Best Practices**

### **For Employees:**
- ✅ Enable GPS before checking in/out
- ⏰ Set reminders matching your work schedule
- 📍 Ensure you're within 100m of the office
- 🔄 Update reminder times if schedule changes

### **For Admins:**
- 📊 Export data regularly for backup
- 🚨 Monitor late alerts during busy periods
- 📈 Use monthly reports for payroll
- 🔧 Test alerts after configuration changes

### **System Maintenance:**
- 🗄️ Database auto-manages attendance records
- 📝 Notification logs stored for audit trail
- 🔄 Automatic timezone handling
- 💾 CSV exports include complete data sets

---

**Made with ❤️ for El Mansoura Team** 