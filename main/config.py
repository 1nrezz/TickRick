import os
from dotenv import load_dotenv
import json

load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "QWERTY!&UU")
DB_NAME = os.getenv("DB_NAME", "discord_bot")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))

SOURCE_CHANNEL = "@TickRick_test"
TARGET_CHANNEL = "@TickRick_target"
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "123456789"))

DELAY = 10
ALBUM_WAIT_TIME = 1.5