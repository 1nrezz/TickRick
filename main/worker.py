import asyncio
import db
from bot import publish_post, bot
from config import DELAY

async def post_worker():
    while True:
        posts = await db.get_scheduled_posts()
        for post in posts:
            if post["mode"].lower() == "manual":
                continue
            delay = post.get('delay_seconds') or DELAY
            try:
                await publish_post(post, bot_instance=bot)
                await db.update_post_status(post["id"], "POSTED")
                print(f"Пост {post['id']} опубликован")
                await asyncio.sleep(delay)
            except Exception as e:
                print(f"Ошибка при публикации {post['id']}: {e}")
                await db.update_post_status(post["id"], "FAILED")
        await asyncio.sleep(5)
