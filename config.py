import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
AUTHORIZED_GUILD_ID = int(os.getenv("AUTHORIZED_GUILD_ID", 0))
START_CHANNEL_ID = int(os.getenv("START_CHANNEL_ID", 0))
SESSION_TIMEOUT_SECONDS = int(os.getenv("SESSION_TIMEOUT_SECONDS", 300))
EMAIL_POLL_INTERVAL = int(os.getenv("EMAIL_POLL_INTERVAL", 5))
PRIVATE_CATEGORY_NAME = os.getenv("PRIVATE_CATEGORY_NAME", "Private TempMail Sessions")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
