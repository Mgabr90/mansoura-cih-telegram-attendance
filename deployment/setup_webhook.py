#!/usr/bin/env python3
"""
Webhook setup script for production deployment
This script sets up the Telegram webhook for the deployed bot
"""

import requests
import os
import sys

def setup_webhook():
    """Set up the webhook for the deployed bot"""
    
    # Get the service URL
    service_url = os.environ.get('RENDER_EXTERNAL_URL')
    if not service_url:
        service_url = input("Enter your Render service URL (e.g., https://your-service.onrender.com): ")
    
    if not service_url.startswith('http'):
        service_url = f"https://{service_url}"
    
    # Remove trailing slash
    service_url = service_url.rstrip('/')
    
    try:
        print(f"🔗 Setting up webhook for: {service_url}")
        
        # Call the webhook setup endpoint
        response = requests.post(f"{service_url}/set-webhook", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Webhook setup successful!")
            print(f"📍 Webhook URL: {data.get('webhook_url')}")
            print(f"💬 Message: {data.get('message')}")
        else:
            print(f"❌ Webhook setup failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error setting up webhook: {e}")
        return False
    
    return True

def check_service_health():
    """Check if the service is running"""
    service_url = os.environ.get('RENDER_EXTERNAL_URL')
    if not service_url:
        service_url = input("Enter your Render service URL: ")
    
    if not service_url.startswith('http'):
        service_url = f"https://{service_url}"
    
    service_url = service_url.rstrip('/')
    
    try:
        print(f"🏥 Checking service health...")
        response = requests.get(f"{service_url}/web-health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service is healthy!")
            print(f"🤖 Bot status: {data.get('bot_status')}")
            print(f"🔗 Webhook ready: {data.get('webhook_ready')}")
            return True
        else:
            print(f"❌ Service health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking service health: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Telegram Bot Webhook Setup")
    print("=" * 40)
    
    # Check service health first
    if check_service_health():
        print("\n" + "=" * 40)
        # Set up webhook
        setup_webhook()
    else:
        print("❌ Service is not healthy. Please check your deployment.")
        sys.exit(1)
    
    print("\n✅ Setup complete!") 