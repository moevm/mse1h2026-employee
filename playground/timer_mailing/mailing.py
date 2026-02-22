import os
from dotenv import load_dotenv
from aiogram import Dispatcher, Bot
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

load_dotenv()
PERIOD_SECONDS = int(os.getenv("MAILING_INTERVAL_SECONDS", 3600))

subscribers: set[int] = set()
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")


def register_mailing(dp: Dispatcher):
    @dp.message(Command("subscribe"))
    async def subscribe_handler(message: Message):
        if message.chat.id in subscribers:
            await message.answer("You have already subscribed to the mailing")
            return

        subscribers.add(message.chat.id)
        await message.answer("You have subscribed to the mailing")

    @dp.message(Command("unsubscribe"))
    async def unsubscribe_handler(message: Message):
        if message.chat.id not in subscribers:
            await message.answer("You are not subscribed to the mailing")
            return

        subscribers.discard(message.chat.id)
        await message.answer("You have unsubscribed from the mailing")


async def send_mailing(bot: Bot):
    if not subscribers:
        return

    text = "Hourly mailing"

    for chat_id in list(subscribers):
        try:
            await bot.send_message(chat_id, text)
        except (TelegramForbiddenError, TelegramBadRequest):
            subscribers.discard(chat_id)
        except Exception as e:
            print(f"Sending error, chat_id={chat_id}: {e}")


def start_scheduler(bot: Bot):
    scheduler.add_job(
        send_mailing,
        trigger=IntervalTrigger(seconds=PERIOD_SECONDS),
        args=[bot],
        id="hourly_mailing",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=5,
    )

    scheduler.start()