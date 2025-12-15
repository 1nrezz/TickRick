import os
from dotenv import load_dotenv
import json

load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

SOURCE_CHANNEL = "@TickRick_test"
TARGET_CHANNEL = "@TickRick_target"