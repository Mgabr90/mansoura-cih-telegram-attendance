# Enhanced Mansoura CIH Telegram Attendance System

A comprehensive, secure attendance tracking system built with Python and Telegram Bot API. Features location-only check-ins, exceptional hours management, real-time admin reporting, and a modern web dashboard.

## 🌟 Features

### 🔒 Security & Compliance
- **Location-only attendance** - Manual GPS entry completely disabled
- **100m radius enforcement** - Must be within office proximity
- **Real-time verification** - GPS coordinates validated instantly
- **Secure conversation state** - Multi-step interactions protected

### 👥 Employee Features
- **Simple check-in/out** via location sharing buttons
- **Automatic late detection** with reason prompts
- **Early departure handling** with mandatory explanations
- **Personal status tracking** and attendance reports
- **Exceptional hours awareness** for custom schedules

### 👨‍💼 Admin Features
- **Daily summary reports** automatically sent at 8 PM
- **Real-time dashboards** with attendance statistics
- **Web-based admin panel** with charts and analytics
- **Exceptional hours management** for individual employees
- **Enhanced late alerts** with employee-provided reasons
- **Employee directory** with comprehensive management
- **Server health monitoring** and activity logging

### 🌐 Web Dashboard Features
- **Modern web interface** with responsive design
- **Real-time analytics** and attendance charts
- **Employee management** with admin controls
- **Report generation** and CSV exports
- **Interactive dashboards** with live data
- **Settings management** and configuration

### 🖥️ Technical Features
- **Dual deployment modes** - Bot only or Bot + Web interface
- **Server wake-up system** (prevents Render free tier sleep)
- **Comprehensive logging** and error handling
- **Database optimization** with proper indexing
- **Graceful shutdown** handling
- **Modular architecture** for easy maintenance

## 📋 Requirements

- Python 3.8+
- Telegram Bot Token
- Internet connection for API calls

## 🚀 Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd "Mansoura CIH Telegram Attendance System"
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.template .env
   # Edit .env with your bot token and settings
   ```

3. **Run the system**:
   
   **Option A: Complete System (Bot + Web Interface)**
   ```bash
   python app.py
   # Access web dashboard at: http://localhost:5000
   ```
   
   **Option B: Telegram Bot Only**
   ```bash
   python run_bot.py
   ```
   
   **Option C: Web Interface Only**
   ```bash
   python run_web.py
   ```

## 🌐 Web Interface

### Access & Login
- **URL**: `http://localhost:5000` (or your deployed domain)
- **Admin Login**: `/login`
- **Default Credentials**: 
  - Username: `admin`
  - Password: `mansoura2024`

### Web Features
- **Dashboard**: Real-time attendance overview
- **Employee Management**: View, edit, and manage employees
- **Reports**: Generate and export attendance reports
- **Analytics**: Charts and statistics
- **Settings**: System configuration

### Web Configuration
Add to your `.env` file:
```env
# Web Interface
WEB_SECRET_KEY=your-secret-key-here
WEB_ADMIN_USER=admin
WEB_ADMIN_PASS=your-secure-password
FLASK_DEBUG=false
```

## 📁 Project Structure

```
attendance_system/
├── core/
│   ├── config.py          # Configuration management
│   ├── database.py        # Database operations
│   └── __init__.py
├── handlers/
│   ├── employee.py        # Employee command handlers
│   ├── admin.py          # Admin command handlers  
│   └── __init__.py
├── services/
│   ├── notification.py    # Notification scheduling
│   ├── health.py         # Health monitoring
│   └── __init__.py
├── utils/
│   ├── location.py       # Location validation
│   ├── keyboards.py      # Telegram keyboards
│   ├── messages.py       # Message formatting
│   └── __init__.py
├── main.py               # Application entry point
└── __init__.py

requirements.txt          # Dependencies
run.py                    # Launcher script
.env                      # Environment configuration
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following settings:

```env
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here

# Office Location (29R3+7Q El Mansoura 1)
OFFICE_LATITUDE=31.0417
OFFICE_LONGITUDE=31.3778
OFFICE_RADIUS=100
OFFICE_ADDRESS=29R3+7Q El Mansoura 1

# Work Hours
DEFAULT_WORK_START=09:00
DEFAULT_WORK_END=17:00

# Server Configuration
PORT=8080
SERVER_URL=http://localhost:8080

# Security
LOCATION_ONLY_ATTENDANCE=true
MANUAL_ENTRY_DISABLED=true

# Development
DEBUG=false
LOG_LEVEL=INFO
```

### Database Schema

The system uses SQLite with the following main tables:

- **employees** - Employee registration and settings
- **attendance** - Daily check-in/out records with reasons
- **admins** - Administrator permissions and settings
- **exceptional_hours** - Custom work schedules
- **conversation_state** - Multi-step interaction handling
- **notification_log** - Sent message tracking
- **server_activity** - System monitoring logs

## 🤖 Bot Commands

### Employee Commands
- `/start` - Welcome message and main keyboard
- `/register` - Register as new employee
- `/status` - View today's attendance status
- `/report` - View recent attendance history
- `/help` - Comprehensive help information
- `/myid` - Get Telegram user ID

### Admin Commands
- `/admin` - Main admin control panel
- `/add_admin <user_id>` - Grant admin privileges
- `/exceptional_hours <user_id> <date> <start> <end> [reason]` - Set custom hours
- `/admin_report` - Real-time attendance dashboard
- `/list_employees` - Employee directory
- `/server_status` - System health and activity logs

## 🔐 Security Features

### Location-Only Attendance
- All check-ins/outs require location sharing
- Manual GPS entry is completely disabled
- Distance verification with configurable radius
- Real-time coordinate validation

### Admin Security
- Role-based access control
- Admin actions logged with timestamps
- Secure conversation state management
- Input validation and sanitization

### Data Protection
- Sensitive data encryption at rest
- Comprehensive audit logging
- Automatic data cleanup routines
- Error handling without data exposure

## 📊 Admin Features

### Daily Summary Reports
Automatically sent to all admins at 8 PM with:
- Total employees and attendance counts
- Late arrivals with reasons
- Early departures with explanations
- Attendance rate calculations

### Real-time Dashboard
- Current day attendance overview
- Employee status monitoring
- Quick action buttons for common tasks
- Interactive employee management

### Exceptional Hours Management
- Set custom work schedules for specific dates
- Override standard work hours
- Reason tracking and audit trails
- Bulk operations support

## 🛠️ Development

### Code Organization
- **Modular architecture** with clear separation of concerns
- **Type hints** throughout for better code maintainability
- **Comprehensive logging** for debugging and monitoring
- **Error handling** with graceful degradation
- **Database abstraction** for easy testing and migration

### Testing
```bash
# Install development dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 🚀 Deployment

### Local Development
```bash
python run.py
```

### Production (Render)
1. Connect GitHub repository to Render
2. Set environment variables in Render dashboard
3. Deploy with build command: `pip install -r requirements.txt`
4. Start command: `python run.py`

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

## 📈 Monitoring

### Health Checks
- `/health` endpoint for service monitoring
- Database activity logging
- Automatic server wake-up (Render compatibility)
- Error rate tracking

### Logging
- Structured logging with timestamps
- Error tracking with stack traces
- Performance metrics collection
- Admin activity auditing

## 🆘 Troubleshooting

### Common Issues

**Bot not responding:**
- Check BOT_TOKEN in .env file
- Verify internet connection
- Check logs for error messages

**Location not accepted:**
- Ensure GPS is enabled on device
- Check OFFICE_RADIUS setting
- Verify OFFICE_LATITUDE/LONGITUDE coordinates

**Admin commands not working:**
- Use `/add_admin <user_id>` to grant privileges
- Check user ID with `/myid` command

### Support
For issues or questions:
1. Check the logs: `tail -f attendance_bot.log`
2. Review configuration in `.env`
3. Verify dependencies: `pip list`
4. Contact system administrator

## 📜 License

This project is proprietary software developed for Mansoura CIH.

## 👥 Credits

Developed for enhanced security and compliance in attendance tracking.

---

**Version:** 2.0.0  
**Last Updated:** 2024  
**Office Location:** 29R3+7Q El Mansoura 1  
**Security Level:** High (Location-only enforcement) 