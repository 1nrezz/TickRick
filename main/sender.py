import tempfile
import os
from telethon.types import Message
from telethon import TelegramClient

async def copy_message(
    msg: Message,
    target_id,
    client: TelegramClient,
    text_override: str | None = None
):
    grouped_id = getattr(msg, "grouped_id", None)

    if grouped_id:
        media = []
        async for m in client.iter_messages(msg.chat_id):
            if m.grouped_id == grouped_id:
                if m.media:
                    media.append(m)

        media.sort(key=lambda x: x.id)

        if media:
            await client.send_file(
                target_id,
                [m.media for m in media],
                caption=text_override or media[0].text
            )
        return

    if msg.media:
        await client.send_file(
            target_id,
            msg.media,
            caption=text_override or msg.text
        )
    elif msg.text:
        await client.send_message(
            target_id,
            text_override or msg.text
        )

async def send_post(post: dict, target_id, client: TelegramClient):
    text = post["text"]

    if post.get("media"):
        temp_files = []

        try:
            for m in post["media"]:
                suffix = {
                    "photo": ".jpg",
                    "video": ".mp4",
                    "gif": ".gif",
                    "sticker": ".webp",
                    "document": ".bin"
                }.get(m["type"], ".bin")

                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                tmp.write(m["file"])
                tmp.close()
                temp_files.append(tmp.name)

            await client.send_file(
                target_id,
                temp_files,
                caption=text
            )

        finally:
            for f in temp_files:
                os.remove(f)

    else:
        msg = await client.get_messages(
            post["source_id"],
            ids=post["source_message_id"]
        )

        await copy_message(
            msg,
            target_id,
            client,
            text_override=text
        )