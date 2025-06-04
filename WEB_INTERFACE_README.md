# 🌐 El Mansoura CIH - Attendance Web Interface

A beautiful, modern web dashboard for managing the Telegram-based attendance system with comprehensive reporting and admin features.

## ✨ Features

### 📊 Dashboard & Analytics
- **Real-time Statistics**: Live attendance rates, check-ins, and employee counts
- **Interactive Charts**: Weekly attendance trends with Chart.js
- **Recent Activity**: Monitor latest employee actions
- **Auto-refresh**: Real-time updates every 30 seconds

### 📈 Advanced Reporting
- **Daily Reports**: Export attendance for specific dates
- **Weekly Reports**: 7-day attendance summaries
- **Monthly Reports**: Comprehensive monthly analytics
- **Custom Reports**: Advanced filtering and date ranges
- **CSV Export**: Download reports in Excel-compatible format

### 👥 Employee Management
- **Employee Directory**: View all registered employees
- **Admin Management**: Add/remove administrator privileges
- **Search & Filter**: Find employees quickly
- **Employee Details**: View attendance summaries and stats

### ⚙️ System Settings
- **Configuration Overview**: View current system settings
- **Environment Variables**: Complete deployment guide
- **System Information**: Database and version details

## 🚀 Quick Deployment on Render

### 1. Prerequisites
- GitHub repository with this code
- Render.com account (free tier available)
- Telegram Bot Token

### 2. Deploy Steps

1. **Create Web Service on Render**
   - Go to [Render.com](https://render.com)
   - Click "New" → "Web Service"
   - Connect your GitHub repository

2. **Configure Build Settings**
   ```
   Build Command: pip install -r web_requirements.txt
   Start Command: python web_interface.py
   ```

3. **Set Environment Variables**
   ```
   BOT_TOKEN=your_telegram_bot_token
   WEB_ADMIN_USER=admin
   WEB_ADMIN_PASS=your_secure_password
   OFFICE_LATITUDE=31.0364
   OFFICE_LONGITUDE=31.3789
   OFFICE_RADIUS=100
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete
   - Access your web interface at the provided URL

## 🔐 Security Features

### Authentication
- **Secure Login**: Username/password protection for admin areas
- **Session Management**: Secure Flask sessions
- **Auto-logout**: Sessions expire for security

### Access Control
- **Admin-only Areas**: Protected routes for sensitive operations
- **Role-based Access**: Different views for admins vs. public

## 📱 Responsive Design

- **Mobile-friendly**: Works perfectly on phones and tablets
- **Modern UI**: Beautiful gradients and animations
- **Bootstrap 5**: Professional, clean interface
- **Font Awesome Icons**: Consistent iconography

## 🛠️ Technical Stack

- **Backend**: Flask (Python)
- **Frontend**: Bootstrap 5, Chart.js, Font Awesome
- **Database**: SQLite (shared with Telegram bot)
- **Charts**: Chart.js for interactive visualizations
- **Export**: Pandas for CSV generation

## 📋 Default Login Credentials

```
Username: admin
Password: mansoura2024
```

⚠️ **Important**: Change these credentials by setting environment variables:
- `WEB_ADMIN_USER`
- `WEB_ADMIN_PASS`

## 🎯 Usage Guide

### For Administrators

1. **Login**: Access the admin panel at `/login`
2. **Dashboard**: View real-time attendance statistics
3. **Reports**: Generate and export various reports
4. **Employee Management**: Add admins and manage users
5. **Settings**: Configure system parameters

### For Public Access

- **Public Dashboard**: View basic attendance statistics
- **System Information**: See office location and working hours
- **Features Overview**: Learn about system capabilities

## 🔧 Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `BOT_TOKEN` | Telegram Bot Token | - | ✅ Yes |
| `WEB_ADMIN_USER` | Admin username | admin | 📝 Recommended |
| `WEB_ADMIN_PASS` | Admin password | mansoura2024 | 📝 Recommended |
| `WEB_SECRET_KEY` | Flask secret key | Auto-generated | 🔄 Optional |
| `OFFICE_LATITUDE` | Office GPS latitude | 31.0364 | 🔄 Optional |
| `OFFICE_LONGITUDE` | Office GPS longitude | 31.3789 | 🔄 Optional |
| `OFFICE_RADIUS` | Attendance radius (m) | 100 | 🔄 Optional |
| `TIMEZONE` | System timezone | Africa/Cairo | 🔄 Optional |
| `PORT` | Web server port | 5000 | 🔄 Optional |

## 📱 API Endpoints

### Public Endpoints
- `GET /` - Public dashboard
- `GET /login` - Admin login page

### Admin API Endpoints
- `GET /api/stats` - Real-time statistics
- `GET /api/attendance-chart` - Chart data
- `GET /api/export/{type}` - Export reports
- `POST /api/employees/{id}/admin` - Manage admin privileges

## 🎨 Customization

### Colors & Themes
The interface uses CSS variables for easy customization:
```css
:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    --success-color: #27ae60;
    --warning-color: #f39c12;
    --danger-color: #e74c3c;
}
```

### Adding New Features
1. Add routes in `web_interface.py`
2. Create templates in `templates/`
3. Add database methods in `database_extensions.py`
4. Update navigation in `base.html`

## 🧪 Testing Locally

```bash
# Install dependencies
pip install -r web_requirements.txt

# Set environment variables
export BOT_TOKEN="your_telegram_bot_token"
export WEB_ADMIN_USER="admin"
export WEB_ADMIN_PASS="your_password"

# Run the web interface
python web_interface.py

# Access at http://localhost:5000
```

## 📊 Features Roadmap

### Current Features
- ✅ Real-time dashboard
- ✅ Employee management
- ✅ Report generation
- ✅ CSV export
- ✅ Admin authentication
- ✅ Responsive design

### Future Enhancements
- 🔄 Advanced filtering
- 🔄 Email notifications
- 🔄 API authentication
- 🔄 Multi-language support
- 🔄 Dark mode theme
- 🔄 Mobile app integration

## 🤝 Integration with Telegram Bot

The web interface shares the same SQLite database with the Telegram bot, providing:

- **Real-time Sync**: Changes reflect immediately
- **Unified Data**: Same employee and attendance records
- **Admin Management**: Web-based admin privileges work in Telegram
- **Report Consistency**: Same data, multiple access methods

## 📞 Support

For issues, questions, or feature requests:

1. **Documentation**: Check this README first
2. **Environment**: Verify all required variables are set
3. **Logs**: Check Render deployment logs for errors
4. **Database**: Ensure the bot has created the SQLite database

## 🎉 Quick Start Summary

1. **Deploy on Render** with the provided configuration
2. **Set environment variables** (especially `BOT_TOKEN`)
3. **Access the interface** at your Render URL
4. **Login with default credentials** (change them!)
5. **Start managing attendance** through the beautiful web interface

---

**Built with ❤️ for El Mansoura CIH**

*Modern attendance management made simple and beautiful.* 