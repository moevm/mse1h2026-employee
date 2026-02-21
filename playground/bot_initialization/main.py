import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# Обработчик команды /start
@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Hello World")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    print("Bot started.")
    asyncio.run(main())
