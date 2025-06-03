# 🤖 El Mansoura Attendance Telegram Bot

A comprehensive Telegram bot for employee attendance tracking based on location verification within a 100-meter radius of the office in El Mansoura.

## 📋 Features

- **Location-based Check-in/Check-out**: Employees must be within 100m of the office location
- **Employee Registration**: Simple registration process via Telegram contact sharing
- **Real-time Attendance Tracking**: Automatic timestamp recording with Cairo timezone
- **Daily Reports**: Individual attendance status and work duration tracking
- **Admin Panel**: Management interface for HR and supervisors
- **Multi-language Support**: Arabic-friendly with emoji indicators
- **Secure Database**: SQLite database for reliable data storage

## 🏢 Office Location

- **Address**: 29R3+7Q El Mansoura 1
- **Coordinates**: 31.0417°N, 31.3778°E
- **Check-in Radius**: 100 meters

## 🚀 Quick Setup

### 1. Prerequisites

- Python 3.8 or higher
- Telegram Bot Token (from @BotFather)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd telegram-attendance-bot

# Install required packages
pip install -r requirements.txt
```

### 3. Configuration

1. Create a new bot with @BotFather on Telegram
2. Copy the bot token
3. Update the `.env` file:

```env
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
OFFICE_LATITUDE=31.0417
OFFICE_LONGITUDE=31.3778
OFFICE_RADIUS=100
DATABASE_NAME=attendance.db
TIMEZONE=Africa/Cairo
```

### 4. Run the Bot

```bash
python bot.py
```

## 📱 How to Use

### For Employees:

1. **Start the bot**: Send `/start` to the bot
2. **Register**: Share your contact information when prompted
3. **Check In**: Press "🟢 Check In" button and share your location
4. **Check Out**: Press "🔴 Check Out" button and share your location
5. **View Status**: Use "📊 My Status" to see today's attendance
6. **Get Report**: Use "📈 My Report" for last 7 days summary

### For Administrators:

1. **Add Admin**: Use `/add_admin <user_id>` to promote users
2. **Admin Panel**: Use `/admin` to access management features
3. **View Reports**: Use `/all_report` to see all employees' attendance

## 🎯 Commands Reference

### User Commands:
- `/start` - Initialize the bot and show main menu
- `/register` - Register as an employee
- `/status` - Check current attendance status
- `/report` - Get personal attendance report (7 days)
- `/help` - Display help information

### Admin Commands:
- `/admin` - Access admin panel
- `/add_admin <user_id>` - Add new administrator
- `/all_report` - View all employees report

## 🗃️ Database Schema

### Tables:
- **employees**: User registration data
- **attendance**: Check-in/out records with timestamps and locations
- **admins**: Administrator access control

## 🔒 Security Features

- **Location Verification**: GPS coordinates validated against office location
- **User Authentication**: Telegram user ID-based authentication
- **Admin Controls**: Role-based access for management functions
- **Data Privacy**: Minimal data collection, secure local storage

## 📊 Attendance Tracking

### Features:
- Real-time location validation (100m radius)
- Automatic work duration calculation
- Prevent duplicate check-ins on same day
- Cairo timezone support
- Detailed attendance history

### Location Requirements:
- GPS must be enabled on device
- User must be within 100 meters of office
- Location sharing permission required

## 🛠️ Technical Details

### Built With:
- **Python 3.8+**
- **python-telegram-bot 20.7**: Telegram Bot API wrapper
- **SQLite3**: Local database storage
- **geopy**: Geographic distance calculations
- **pytz**: Timezone handling
- **python-dotenv**: Environment configuration

### Architecture:
- **Modular Design**: Separate modules for database, location, and bot logic
- **Async Operations**: Non-blocking message handling
- **Error Handling**: Comprehensive error management and user feedback
- **Scalable**: Easy to extend with additional features

## 📈 Reporting Features

### Individual Reports:
- Daily attendance status
- Work duration tracking
- 7-day attendance history
- Check-in/out timestamps

### Admin Reports:
- All employees daily summary
- Attendance status overview
- Employee management
- Real-time monitoring

## 🌍 Localization

- **Timezone**: Africa/Cairo (Egypt Standard Time)
- **Language**: English with Arabic-friendly emoji
- **Date Format**: ISO 8601 standard
- **Time Display**: 24-hour format

## 🔧 Customization

### Environment Variables:
- `OFFICE_LATITUDE`: Office latitude coordinate
- `OFFICE_LONGITUDE`: Office longitude coordinate  
- `OFFICE_RADIUS`: Attendance radius in meters
- `TIMEZONE`: Local timezone for timestamps

### Adding Features:
- Extend `AttendanceDatabase` class for new data operations
- Add handlers in `AttendanceBot.setup_handlers()`
- Implement new commands following existing patterns

## 🚨 Troubleshooting

### Common Issues:

1. **Bot not responding**:
   - Check BOT_TOKEN in .env file
   - Verify internet connection
   - Check console for error messages

2. **Location not accepted**:
   - Ensure GPS is enabled
   - Check if within 100m radius
   - Verify coordinates accuracy

3. **Registration failed**:
   - Make sure to share contact information
   - Check if already registered
   - Contact administrator

## 📞 Support

For technical support or feature requests:
- Check the troubleshooting section
- Review error logs
- Contact system administrator

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Telegram Bot API for excellent documentation
- geopy library for accurate distance calculations
- El Mansoura team for requirements and testing

---

**Made with ❤️ for El Mansoura Team** 