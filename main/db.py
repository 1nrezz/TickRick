import asyncpg
import json
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

db_pool: asyncpg.Pool | None = None


# =========================
# INIT
# =========================

async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        min_size=1,
        max_size=10
    )

    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            source_chat VARCHAR NOT NULL,
            source_message_id BIGINT NOT NULL,
            content_type VARCHAR NOT NULL,
            text TEXT,
            media JSONB,
            grouped_id BIGINT,
            mode VARCHAR NOT NULL DEFAULT 'AUTO',
            status VARCHAR NOT NULL DEFAULT 'NEW',
            delay_seconds INTEGER,
            publish_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """)

    print("✅ База данных готова")


# =========================
# POSTS
# =========================

async def add_post(
    source_chat: str,
    source_message_id: int,
    content_type: str,
    text: str | None = None,
    media: list | None = None,
    grouped_id: int | None = None,
    mode: str = "AUTO",
    status: str = "NEW",
    delay_seconds: int = None,
    publish_at = None

):
    async with db_pool.acquire() as conn:
        post_id = await conn.fetchval(
            """
            INSERT INTO posts (
                source_chat,
                source_message_id,
                content_type,
                text,
                media,
                grouped_id, 
                mode,
                status, delay_seconds, publish_at
            )
            VALUES ($1,$2,$3,$4,$5::jsonb,$6,$7,$8,$9,$10)
            RETURNING id
            """,
            source_chat,
            source_message_id,
            content_type,
            text,
            json.dumps(media) if media else None,
            grouped_id,
            mode, status, delay_seconds, publish_at
        )
        return post_id


async def get_post_by_id(post_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM posts WHERE id=$1",
            post_id
        )
        return _normalize_post(row)


async def get_post_by_source_id(source_message_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM posts WHERE source_message_id=$1",
            source_message_id
        )
        return _normalize_post(row)


# =========================
# UPDATE
# =========================

async def update_post_status(post_id: int, status: str):
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE posts
            SET status=$2, updated_at=NOW()
            WHERE id=$1
            """,
            post_id,
            status
        )


async def update_post_media(post_id: int, media: list):
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE posts
            SET media=$2::jsonb, updated_at=NOW()
            WHERE id=$1
            """,
            post_id,
            json.dumps(media)
        )


# =========================
# DELAY / PUBLISH
# =========================

async def set_post_delay(post_id: int, delay_seconds: int, publish_at):
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE posts
            SET delay_seconds=$2,
                publish_at=$3,
                status='SCHEDULED',
                updated_at=NOW()
            WHERE id=$1
            """,
            post_id,
            delay_seconds,
            publish_at
        )


async def get_scheduled_posts():
    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT * FROM posts
            WHERE status='SCHEDULED'
              AND publish_at <= NOW()
            ORDER BY publish_at
            """
        )
        return [_normalize_post(r) for r in rows]


async def mark_post_posted(post_id: int):
    async with db_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE posts
            SET status='POSTED',
                updated_at=NOW()
            WHERE id=$1
            """,
            post_id
        )


# =========================
# HELPERS
# =========================

def _normalize_post(row):
    if not row:
        return None

    post = dict(row)

    if post.get("media"):
        post["media"] = json.loads(post["media"])

    return post
