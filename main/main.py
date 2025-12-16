import config
import db
import asyncio
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.types import BotCommand
from reader import start_userbot
from worker import post_worker
from bot import bot, callback_handler, dp, fsm_edit_text_handler, fsm_delay_handler
from states import PostStates
from aiogram import F

async def set_commands(bot):
    commands = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="help", description="Помощь"),
    ]
    await bot.set_my_commands(commands)

@dp.message(Command("start"))
async def start(msg: Message):
    await msg.answer("Привет!")


async def main():
    await db.init_db()
    asyncio.create_task(start_userbot())

    asyncio.create_task(post_worker())

    dp.callback_query.register(callback_handler)
    dp.message.register(fsm_edit_text_handler, F.state == PostStates.editing_text)
    dp.message.register(fsm_delay_handler, F.state == PostStates.setting_delay)

    await set_commands(bot)
    try:
        await dp.start_polling(bot)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await bot.session.close()
        print("Сессия бота закрыта")

print(1)
asyncio.run(main())