import sys
import os

# Add src directory to path
sys.path.insert(0, 'src')

print("sys.path:", sys.path[:3])

try:
    print("Trying to import config...")
    import config
    print("Config module imported:", config)
    print("Config attributes:", dir(config))
    
    if hasattr(config, 'Config'):
        print("Config.Config found!")
        Config = config.Config
        print("BOT_TOKEN:", getattr(Config, 'BOT_TOKEN', 'Not found'))
    else:
        print("Config.Config not found")
        
except Exception as e:
    print("Error importing config:", e)

try:
    print("\nTrying direct import from src/config.py...")
    from src.config import Config
    print("Direct import successful!")
    print("BOT_TOKEN:", getattr(Config, 'BOT_TOKEN', 'Not found'))
except Exception as e:
    print("Error with direct import:", e) 