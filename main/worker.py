import asyncio
import db
from sender import send_post
from config import TARGET_CHANNELS
from bot import client

async def post_worker():
    while True:
        settings = await db.get_settings()

        if settings["mode"] != "AUTO":
            await asyncio.sleep(5)
            continue

        delay = settings["delay_seconds"]
        posts = await db.get_unpublished_posts()

        for post in posts:
            for target in TARGET_CHANNELS:
                await send_post(post, target, client)
            await db.update_post_status(post["id"], "POSTED")
            await asyncio.sleep(delay)

        await asyncio.sleep(5)
