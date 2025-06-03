# 🏢 Mansoura CIH Telegram Attendance System

A comprehensive Telegram bot for employee attendance tracking with GPS location verification, specifically designed for Mansoura CIH office operations.

## 🌟 Key Features

- **Location-verified check-in/check-out** (100m radius)
- **Admin-only CSV export system** with multiple formats
- **Automated reminder system** for employees
- **Real-time admin alerts** for late/missed attendance
- **Modular architecture** (80% code reduction)

## 📁 Project Structure

```
src/               # Source code (modular architecture)
docs/              # Complete documentation
deployment/        # Deployment files & configurations
.env.template      # Environment configuration template
README.md          # This file
```

## 🚀 Quick Start

1. **Install**: `pip install -r deployment/requirements.txt`
2. **Configure**: Copy `.env.template` to `src/.env` and edit
3. **Setup Admin**: `cd src && python setup_admin.py`
4. **Run**: `cd src && python main_bot.py`

## 📋 Usage

### Employees:
- `/start` - Register with contact sharing
- Share location to check in/out
- `/status` - View attendance status
- `/reminders` - Manage personal reminders

### Admins:
- `/admin` - Access admin panel
- `/export_daily`, `/export_monthly` - Export reports
- `/admin_alerts` - Manage alert settings

## 🏢 Office Location

**Mansoura CIH Office**: 29R3+7Q El Mansoura 1, Egypt  
**GPS**: 29.5889°N, 31.2554°E  
**Radius**: 100 meters  

## 📚 Documentation

See `docs/` directory for complete documentation:
- Setup Guide (`docs/README.md`)
- Architecture Details (`docs/ARCHITECTURE.md`) 
- Features Guide (`docs/FEATURES_GUIDE.md`)
- Deployment Instructions (`docs/DEPLOYMENT.md`)

## 🚀 Deployment Options

- 🐳 Docker
- ☁️ Render (auto-deploy)
- 🚀 Heroku
- 💻 Local

---

**Ready for Production!** Made with ❤️ for Mansoura CIH Team 