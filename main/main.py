import config
import db
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.types import BotCommand
from reader import get_last_post
from bot import publish_post

bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

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
    post = await get_last_post()
    if post and post.text:
        await publish_post(post.text)


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