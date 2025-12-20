from telethon import events
from config import SOURCE_CHANNELS, BOT_USER_ID
import db
from bot import send_notification, client
from sender import copy_message

handled_groups: set[int] = set()

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def new_post_handler(event):
    msg = event.message

    if msg.grouped_id:
        if msg.grouped_id in handled_groups:
            return
        handled_groups.add(msg.grouped_id)

    post_id = await db.add_post(
        source_id=event.chat_id,
        source_name=event.chat.username or event.chat.title,
        source_message_id=msg.id,
        text=msg.text,
        grouped_id=msg.grouped_id
    )

    post = await db.get_post_by_id(post_id)
    settings = await db.get_settings()

    if settings["mode"] == "MANUAL":
        await send_notification(post)
        await copy_message(msg, BOT_USER_ID, client)


async def start_userbot():
    await client.start()
    print("Userbot started")
    await client.run_until_disconnected()
