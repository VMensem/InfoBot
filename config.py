# config/config.py
import os

API_URL = os.getenv("API_URL", "https://api.depscian.tech/v2/player")
API_KEY = os.getenv("API_KEY", "")
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "10"))

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
DISCORD_COMMAND_PREFIX = os.getenv("DISCORD_COMMAND_PREFIX", "!")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
