from dataclasses import dataclass
from datetime import time
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import ReminderConfig
from constants.texts import END_WORK_REMINDER_TEXT, START_WORK_REMINDER_TEXT
from services.auth_service import AuthService


def parse_reminder_time(value: str):
    try:
        return time.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"Некорректный формат времени напоминания: {value}. Ожидается HH:MM"
        ) from exc
    

@dataclass(frozen=True)
class ReminderTask:
    title: str
    trigger_time: time
    message: str


class ReminderService:
    def __init__(self, auth_service: AuthService, config: ReminderConfig):
        self.auth_service = auth_service
        self.timezone = ZoneInfo(config.timezone)
        self.days_of_week = config.days_of_week
        self.tasks = [
            ReminderTask(
                title="start_work",
                trigger_time=parse_reminder_time(config.morning_time),
                message=START_WORK_REMINDER_TEXT,
            ),
            ReminderTask(
                title="end_work",
                trigger_time=parse_reminder_time(config.evening_time),
                message=END_WORK_REMINDER_TEXT,
            ),
        ]
        self.scheduler = AsyncIOScheduler(timezone=self.timezone)
        self._started = False

    async def start(self, bot: Bot):
        if self._started:
            return

        for task in self.tasks:
            self.scheduler.add_job(
                self.send_reminder,
                trigger=CronTrigger(
                    hour=task.trigger_time.hour,
                    minute=task.trigger_time.minute,
                    day_of_week=self.days_of_week,
                    timezone=self.timezone,
                ),
                kwargs={"bot": bot, "task": task},
                id=f"reminder:{task.title}",
                replace_existing=True,
                coalesce=True,
                misfire_grace_time=15 * 60,
                max_instances=1,
            )

        self.scheduler.start()
        self._started = True

    async def stop(self):
        if not self._started:
            return

        self.scheduler.shutdown(wait=False)
        self._started = False

    async def send_reminder(self, bot: Bot, task: ReminderTask):
        user_ids = self.auth_service.get_user_ids()

        if not user_ids:
            return

        for user_id in user_ids:
            try:
                await bot.send_message(chat_id=user_id, text=task.message, parse_mode="HTML")
            except TelegramAPIError as e:
                print(f"Не удалось отправить напоминание user_id={user_id}: {e}")