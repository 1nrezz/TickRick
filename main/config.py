import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")

DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))

SOURCE_CHANNELS = [" ", " ", ] #без пробелов если нет в названии и тут без @
TARGET_CHANNELS = ["@ ", "@ "] #оже самое только с @

BOT_USER_ID = "@" #юзернейм бота
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "123456789"))
