import os
from dotenv import load_dotenv

# Load from current directory
load_dotenv('.env')

print("Current directory:", os.getcwd())
print("BOT_TOKEN from env:", os.getenv('BOT_TOKEN'))
print("OFFICE_LATITUDE from env:", os.getenv('OFFICE_LATITUDE'))

# Test the bot_config import
import sys
sys.path.insert(0, 'src')

from bot_config import Config
print("BOT_TOKEN from Config:", Config.BOT_TOKEN)
print("OFFICE_LATITUDE from Config:", Config.OFFICE_LATITUDE) 