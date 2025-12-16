from aiogram import Bot, types, Dispatcher
from config import BOT_TOKEN, ADMIN_USER_ID, TARGET_CHANNEL
import tempfile
from aiogram.types import FSInputFile, InputMediaPhoto, InputMediaVideo
from aiogram.fsm.context import FSMContext
import db
from states import PostStates

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# -------------------------------
# Вспомогательная функция определения типа контента
# -------------------------------
def get_content_type(msg):
    if msg.photo:
        return "photo"
    elif msg.video:
        return "video"
    elif msg.animation:
        return "gif"
    elif msg.sticker:
        return "sticker"
    elif msg.document:
        return "document"
    elif msg.text:
        return "text"
    return "unknown"


# -------------------------------
# Уведомление о новом посте в ЛС
# -------------------------------
async def send_notification(post):
    text = f"📥 Новый пост получен\n\n"
    text += f"Тип: {post['content_type']}\n"
    if post['text']:
        text += f"Текст: {post['text'][:200]}...\n"
    text += f"ID сообщения: {post['id']}"

    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{post['id']}"),
                types.InlineKeyboardButton(text="🖼 Медиа", callback_data=f"media:{post['id']}"),
                types.InlineKeyboardButton(text="⏱ Установить delay", callback_data=f"delay:{post['id']}"),
                types.InlineKeyboardButton(text="🚀 Опубликовать", callback_data=f"publish:{post['id']}")
            ]
        ]
    )

    await bot.send_message(
        chat_id=ADMIN_USER_ID,
        text=text,
        reply_markup=keyboard
    )


# -------------------------------
# Функция публикации поста в ЛС
# -------------------------------
async def publish_post(post, chat_id=None, bot_instance=None):
    if not post:
        return

    if bot_instance is None:
        bot_instance = bot

    content_type = post["content_type"]
    media = post["media"]
    text = post["text"] or ""

    # Текстовое сообщение
    if content_type == "text" and not media:
        await bot_instance.send_message(
            chat_id=chat_id,
            text=text
        )
        return

    # Медиа / альбом
    if media:
        if len(media) > 1:
            await publish_album(media, text, bot_instance, chat_id=chat_id)
            return

        media_item = media[0]
        if media_item["file"] is None:
            print(f"❌ Медиа для типа {media_item['type']} отсутствует, публикация пропущена")
            return
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(media_item["file"])
            f.flush()
            file = FSInputFile(f.name)
            caption = text or ""

            if media_item["type"] == "sticker":
                await bot_instance.send_sticker(chat_id=chat_id, sticker=file)
            elif media_item["type"] == "gif":
                await bot_instance.send_animation(chat_id=chat_id, animation=file, caption=caption)
            elif media_item["type"] == "video":
                await bot_instance.send_video(chat_id=chat_id, video=file, caption=caption)
            elif media_item["type"] == "photo":
                await bot_instance.send_photo(chat_id=chat_id, photo=file, caption=caption)
            elif media_item["type"] == "document":
                await bot_instance.send_document(chat_id=chat_id, document=file, caption=caption)

async def publish_album(media_list, caption="", chat_id=None, bot_instance=None):
    if bot_instance is None:
        bot_instance = bot
    media_group = []
    for i, media_item in enumerate(media_list):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(media_item["file"])
            f.flush()
            file = FSInputFile(f.name)
            if media_item["type"] == "photo":
                media_group.append(InputMediaPhoto(media=file, caption=caption if i == 0 else ""))
            elif media_item["type"] == "video":
                media_group.append(InputMediaVideo(media=file, caption=caption if i == 0 else ""))
    if media_group:
        await bot_instance.send_media_group(chat_id=chat_id, media=media_group)


# -------------------------------
# Callback handler
# -------------------------------
@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery, state: FSMContext):
    action, post_id = callback.data.split(":")
    post_id = int(post_id)
    post = await db.get_post_by_id(post_id)

    if not post:
        await callback.message.answer(f"Пост с ID {post_id} не найден в базе!")
        await callback.answer()
        return

    if action == "edit":
        await callback.message.answer(f"Введите новый текст для поста {post_id}:")
        await state.update_data(post_id=post_id)
        await state.set_state(PostStates.editing_text)
    elif action == "media":
        await callback.message.answer(
            "Отправь НОВОЕ медиа (фото / видео / gif / документ / стикер), которое заменит текущее"
        )
        await state.update_data(post_id=post_id)
        await state.set_state(PostStates.replacing_media)
    elif action == "delay":
        await callback.message.answer(f"Введите задержку в секундах для поста {post_id}:")
        await state.update_data(post_id=post_id)
        await state.set_state(PostStates.setting_delay)
    elif action == "publish":
        await publish_post(post, TARGET_CHANNEL)
        await db.update_post_status(post_id, "POSTED")
        await callback.message.answer(f"Пост {post_id} опубликован в канал {TARGET_CHANNEL}!")

    await callback.answer()


# -------------------------------
# FSM: редактирование текста
# -------------------------------
@dp.message(PostStates.editing_text)
async def fsm_edit_text_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    post_id = data.get("post_id")
    new_text = message.text
    async with db.db_pool.acquire() as conn:
        await conn.execute("UPDATE posts SET text=$1, updated_at=NOW() WHERE id=$2", new_text, post_id)
        await db.update_post_status(post_id, "EDITED")
    await message.answer(f"Текст поста {post_id} обновлен.")
    await state.clear()


# -------------------------------
# FSM: установка delay
# -------------------------------
@dp.message(PostStates.setting_delay)
async def fsm_delay_handler(message: types.Message, state: FSMContext):
    data = await state.get_data()
    post_id = data.get("post_id")
    try:
        delay_sec = int(message.text)
        await db.set_post_delay(post_id, delay_sec)
        await message.answer(f"Задержка для поста {post_id} установлена: {delay_sec} сек.")
    except ValueError:
        await message.answer("Введите число в секундах.")
    await state.clear()


# -------------------------------
# FSM: замена медиа
# -------------------------------
@dp.message(PostStates.replacing_media)
async def fsm_replace_media(message: types.Message, state: FSMContext):
    data = await state.get_data()
    post_id = data["post_id"]

    media = None
    media_type = None

    if message.photo:
        media = message.photo[-1]
        media_type = "photo"
    elif message.video:
        media = message.video
        media_type = "video"
    elif message.animation:
        media = message.animation
        media_type = "gif"
    elif message.document:
        media = message.document
        media_type = "document"
    elif message.sticker:
        media = message.sticker
        media_type = "sticker"
    else:
        await message.answer("❌ Поддерживается только фото, видео, gif, стикер или документ")
        return

    file = await bot.get_file(media.file_id)
    file_bytes = await bot.download_file(file.file_path)

    media_json = [{
        "type": media_type,
        "file": file_bytes.read()
    }]

    async with db.db_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE posts
            SET media=$1, content_type=$2, updated_at=NOW()
            WHERE id=$3
            """,
            media_json, media_type, post_id
        )

    await message.answer(f"✅ Медиа для поста {post_id} заменено")
    await state.clear()
