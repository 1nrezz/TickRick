import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from telethon import TelegramClient
import db
from states import PostStates
from sender import send_post
from config import BOT_TOKEN, ADMIN_USER_ID, TARGET_CHANNELS, API_ID, API_HASH, BOT_USER_ID

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

client = TelegramClient("session", API_ID, API_HASH)

async def send_notification(post):
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[[
            types.InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{post['id']}"),
            types.InlineKeyboardButton(text="🚀 Опубликовать", callback_data=f"publish:{post['id']}")
        ]]
    )

    await bot.send_message(
        ADMIN_USER_ID,
        f"📥 Новый пост\n\nID: {post['id']}\n\n{post['text'] or ''}",
        reply_markup=keyboard
    )

@dp.callback_query()
async def callback_handler(cb: types.CallbackQuery, state: FSMContext):
    action, post_id = cb.data.split(":")
    post_id = int(post_id)

    post = await db.get_post_by_id(post_id)
    if not post:
        await cb.message.answer("❌ Пост не найден")
        return

    if action == "edit":
        await state.update_data(post_id=post_id)
        await state.set_state(PostStates.editing_text)
        await cb.message.answer("Введите новый текст:")

    elif action == "publish":
        settings = await db.get_settings()
        delay = settings["delay_seconds"]

        await cb.message.answer(f"⏳ Публикация через {delay} сек.")
        await asyncio.sleep(delay)

        post = await db.get_post_by_id(post_id)
        for target in TARGET_CHANNELS:
            await send_post(post, target, client)
        await db.update_post_status(post_id, "POSTED")

        await cb.message.answer("✅ Опубликовано")

    await cb.answer()

@dp.message(PostStates.editing_text)
async def fsm_edit_text_handler(msg: types.Message, state: FSMContext):
    if msg.from_user.id != ADMIN_USER_ID:
        return
    data = await state.get_data()
    post_id = data.get("post_id")

    if not post_id:
        await msg.answer("❌ Сессия устарела")
        await state.clear()
        return

    await db.update_post_text(post_id, msg.text)

    post = await db.get_post_by_id(post_id)
    await state.clear()
    await send_post(post, BOT_USER_ID, client)

    await msg.answer("✏️ Текст обновлён")

@dp.message(Command("get_status"))
async def get_status(msg: types.Message):
    s = await db.get_settings()
    await msg.answer(
        f"⚙️ Статус\n\n"
        f"Режим: {s['mode']}\n"
        f"Delay: {s['delay_seconds']} сек\n\n"
    )

@dp.message(Command("mode_manual"))
async def mode_manual(msg: types.Message):
    await db.set_mode("MANUAL")
    await msg.answer("🟡 Ручной режим")

@dp.message(Command("mode_auto"))
async def mode_auto(msg: types.Message):
    await db.set_mode("AUTO")
    await msg.answer("🟢 Авто режим")

@dp.message(Command("set_delay"))
async def set_delay(msg: types.Message):
    try:
        delay = int(msg.text.split()[1])
        await db.set_delay(delay)
        await msg.answer(f"⏱ Delay установлен: {delay} сек")
    except:
        await msg.answer("Использование: /set_delay 60")