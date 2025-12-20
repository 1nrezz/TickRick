import db
import asyncio
from aiogram.types import BotCommand
from reader import start_userbot
from worker import post_worker
from bot import bot, dp

async def set_commands(bot):
    commands = [
        BotCommand(command="get_status", description="Статус"),
        BotCommand(command="set_delay", description="Установить задержу между отправлениями"),
        BotCommand(command="mode_manual", description="Ручное управление"),
        BotCommand(command="mode_auto", description="Автоматическое управление")
    ]
    await bot.set_my_commands(commands)

async def main():
    await db.init_db()
    asyncio.create_task(start_userbot())

    asyncio.create_task(post_worker())

    await set_commands(bot)
    try:
        await dp.start_polling(bot)
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        await bot.session.close()
        print("Сессия бота закрыта")

asyncio.run(main())
