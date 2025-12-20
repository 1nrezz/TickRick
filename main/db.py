import asyncpg
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

db_pool: asyncpg.Pool | None = None

async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
    )

    async with db_pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            source_id BIGINT,
            source_name TEXT,
            source_message_id BIGINT,
            text TEXT,
            grouped_id BIGINT,
            status TEXT DEFAULT 'NEW',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """)

        await conn.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id BOOLEAN PRIMARY KEY DEFAULT TRUE,
            mode TEXT DEFAULT 'MANUAL',
            delay_seconds INTEGER DEFAULT 0
        )
        """)

        await conn.execute("""
        INSERT INTO settings (id)
        VALUES (TRUE)
        ON CONFLICT (id) DO NOTHING
        """)


async def add_post(**kwargs) -> int:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("""
        INSERT INTO posts (source_id, source_name, source_message_id, text, grouped_id)
        VALUES ($1,$2,$3,$4,$5)
        RETURNING id
        """,
        kwargs["source_id"],
        kwargs["source_name"],
        kwargs["source_message_id"],
        kwargs.get("text"),
        kwargs.get("grouped_id")
        )
        return row["id"]

async def get_post_by_id(post_id: int):
    async with db_pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM posts WHERE id=$1",
            post_id
        )

async def get_unpublished_posts():
    async with db_pool.acquire() as conn:
        return await conn.fetch(
            "SELECT * FROM posts WHERE status='NEW' ORDER BY id"
        )

async def update_post_text(post_id: int, text: str):
    async with db_pool.acquire() as conn:
        await conn.execute("""
        UPDATE posts
        SET text=$1, updated_at=NOW(), status='EDITED'
        WHERE id=$2
        """, text, post_id)


async def update_post_status(post_id: int, status: str):
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE posts SET status=$1 WHERE id=$2",
            status, post_id
        )

async def get_settings():
    async with db_pool.acquire() as conn:
        return await conn.fetchrow("SELECT * FROM settings WHERE id=TRUE")


async def set_mode(mode: str):
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE settings SET mode=$1 WHERE id=TRUE",
            mode
        )

async def set_delay(delay: int):
    async with db_pool.acquire() as conn:
        await conn.execute(
            "UPDATE settings SET delay_seconds=$1 WHERE id=TRUE",
            delay
        )
