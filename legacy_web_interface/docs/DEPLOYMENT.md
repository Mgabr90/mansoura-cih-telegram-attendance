# 🚀 Deployment Guide - El Mansoura Attendance Bot

This guide covers multiple deployment options for your Telegram attendance bot.

## 🌟 Render.com (Recommended - Free Tier)

Render is perfect for this bot because it offers:
- Free tier with 750 hours/month
- Automatic HTTPS
- Persistent storage
- Easy environment variable management
- GitHub integration

### Step-by-Step Render Deployment:

1. **Prepare Your Repository**:
   ```bash
   # Make sure all files are committed
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Create Render Account**:
   - Go to [render.com](https://render.com)
   - Sign up with GitHub account

3. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository with your bot code

4. **Configure Service**:
   - **Name**: `el-mansoura-attendance-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
   - **Plan**: `Free`

5. **Set Environment Variables**:
   Go to Environment tab and add:
   ```
   BOT_TOKEN=your_actual_bot_token_here
   OFFICE_LATITUDE=31.0417
   OFFICE_LONGITUDE=31.3778
   OFFICE_RADIUS=100
   DATABASE_NAME=attendance.db
   TIMEZONE=Africa/Cairo
   ```

6. **Deploy**:
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Check logs for any errors

### Important Notes for Render:
- Database file will persist between deployments
- Logs are available in the dashboard
- Free tier sleeps after 15 minutes of inactivity
- Bot will auto-wake when someone sends a message

---

## 🔷 Railway.app Alternative

Railway is another great option with generous free tier:

1. **Create Account**: [railway.app](https://railway.app)
2. **Deploy from GitHub**:
   - Connect GitHub repository
   - Railway auto-detects Python
3. **Add Environment Variables** in the Variables tab
4. **Deploy** automatically

---

## 🟣 Heroku Alternative

Heroku is reliable but has limited free tier:

1. **Install Heroku CLI**
2. **Login and Create App**:
   ```bash
   heroku login
   heroku create el-mansoura-attendance-bot
   ```
3. **Set Environment Variables**:
   ```bash
   heroku config:set BOT_TOKEN=your_bot_token
   heroku config:set OFFICE_LATITUDE=31.0417
   heroku config:set OFFICE_LONGITUDE=31.3778
   heroku config:set OFFICE_RADIUS=100
   ```
4. **Deploy**:
   ```bash
   git push heroku main
   ```

---

## 🖥️ VPS Deployment (DigitalOcean, Linode, etc.)

For more control and always-on service:

### Ubuntu Server Setup:

1. **Update System**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Python and Git**:
   ```bash
   sudo apt install python3 python3-pip git -y
   ```

3. **Clone Repository**:
   ```bash
   git clone <your-repo-url>
   cd telegram-attendance-bot
   ```

4. **Install Dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

5. **Set Environment Variables**:
   ```bash
   # Create .env file with your actual values
   nano .env
   ```

6. **Create Systemd Service**:
   ```bash
   sudo nano /etc/systemd/system/attendance-bot.service
   ```
   
   Add this content:
   ```ini
   [Unit]
   Description=El Mansoura Attendance Bot
   After=network.target
   
   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/telegram-attendance-bot
   Environment=PATH=/usr/bin:/usr/local/bin
   ExecStart=/usr/bin/python3 bot.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```

7. **Start Service**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable attendance-bot
   sudo systemctl start attendance-bot
   ```

---

## 📱 Testing Your Deployment

After deployment, test your bot:

1. **Find Your Bot**: Search for your bot username on Telegram
2. **Send `/start`**: Should get welcome message
3. **Register**: Test the registration process
4. **Location Test**: Try check-in with location (you can test anywhere first)

### Monitoring:
- Check deployment logs regularly
- Monitor bot responses
- Test all commands periodically

---

## 🔧 Troubleshooting

### Common Issues:

1. **Bot Not Responding**:
   - Check if BOT_TOKEN is correctly set
   - Verify deployment logs
   - Ensure service is running

2. **Database Errors**:
   - Check file permissions
   - Verify SQLite is working
   - Check disk space

3. **Location Issues**:
   - Verify OFFICE_LATITUDE/LONGITUDE values
   - Test with correct coordinates
   - Check geopy installation

4. **Service Sleeping (Render/Heroku)**:
   - Free tiers sleep after inactivity
   - Consider upgrading for 24/7 service
   - Use cron job to keep alive

### Logs Access:
- **Render**: Dashboard → Service → Logs
- **Railway**: Dashboard → Deployments → Logs  
- **Heroku**: `heroku logs --tail`
- **VPS**: `sudo journalctl -u attendance-bot -f`

---

## 💡 Recommendations

### For Small Teams (< 50 employees):
- **Render Free Tier** (750 hours/month)
- Easy setup and management

### For Medium Teams (50-200 employees):
- **Railway Pro** ($5/month)
- Better uptime and performance

### For Large Organizations (200+ employees):
- **VPS Solution** ($5-20/month)
- Full control and guaranteed uptime
- Backup and monitoring setup

### Production Considerations:
- Regular database backups
- Monitoring and alerting
- SSL certificates (handled by Render/Railway)
- Error logging and monitoring

---

## 🔐 Security Checklist

- ✅ Bot token stored as environment variable
- ✅ Database not exposed publicly
- ✅ HTTPS enabled (automatic on cloud platforms)
- ✅ Regular security updates
- ✅ Admin access controlled
- ✅ Location verification enabled

---

Choose the deployment method that best fits your needs and budget. Render is recommended for getting started quickly with minimal setup!