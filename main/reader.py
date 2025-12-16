from telethon import TelegramClient, events
from config import API_ID, API_HASH, SOURCE_CHANNEL, ALBUM_WAIT_TIME

from bot import send_notification
import db
import json
import asyncio

client = TelegramClient("session", API_ID, API_HASH)

@client.on(events.NewMessage(chats=SOURCE_CHANNEL))
async def new_post_handler(event):
    msg = event.message

    # Определяем тип контента
    if msg.photo:
        content_type = "photo"
    elif msg.video:
        content_type = "video"
    elif msg.gif:
        content_type = "gif"
    elif msg.sticker:
        content_type = "sticker"
    elif msg.document:
        content_type = "document"
    elif msg.text:
        content_type = "text"
    else:
        content_type = "unknown"

    # Сохраняем медиа пути в JSON
    media_list = []
    if msg.media:
        media_list.append({"type": content_type, "file": None})  # файл пока None, загрузим позже

    grouped_id = getattr(msg, "grouped_id", None)

    # Сохраняем пост в БД
    post_id = await db.add_post(
        source_chat=SOURCE_CHANNEL,
        source_message_id=msg.id,
        content_type=content_type,
        text=msg.text,
        media=media_list if media_list else None,
        grouped_id=grouped_id,
        mode="AUTO",           # по умолчанию авто
        status="NEW",          # новый пост
        delay_seconds=None,
        publish_at=None
    )

    # if not post:
    #     post = await db.get_post_by_source_id(msg.id)
    post = await db.get_post_by_id(post_id)
    if not post:
        print(f"Ошибка: не удалось получить пост {msg.id} из БД")
        return

    print(f"Новый пост сохранён в БД: {post['id']}")
    await send_notification(post)

async def start_userbot():
    await client.start()
    print("Userbot запущен")
    await client.run_until_disconnected()