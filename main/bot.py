from aiogram import Bot
from config import BOT_TOKEN, TARGET_CHANNEL

bot = Bot(token=BOT_TOKEN)

async def publish_post(text):
    await bot.send_message(
        chat_id=TARGET_CHANNEL,
        text=text
    )