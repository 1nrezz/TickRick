from telethon import TelegramClient
from config import API_ID, API_HASH, SOURCE_CHANNEL

client = TelegramClient("session", API_ID, API_HASH)


async def get_last_post():
    await client.start()
    async for msg in client.iter_messages(SOURCE_CHANNEL, limit=1):
        print("Последний пост найден:")
        return msg