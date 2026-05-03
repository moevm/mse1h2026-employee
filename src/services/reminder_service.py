import re
from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import ReminderConfig
from constants.texts import END_WORK_REMINDER_TEXT, START_WORK_REMINDER_TEXT
from services.auth_service import AuthService


def parse_reminder_time(value: str):
    value = str(value).strip()

    match = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", value)
    if not match:
        raise ValueError(
            f"Некорректный формат времени напоминания: {value}. Ожидается HH:MM"
        )

    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = int(match.group(3) or 0)

    if hours > 23 or minutes > 59 or seconds > 59:
        raise ValueError(
            f"Некорректное время напоминания: {value}. Ожидается HH:MM"
        )

    return time(hour=hours, minute=minutes)


@dataclass(frozen=True)
class ReminderTask:
    title: str
    message: str
    settings_key: str
    default_time: time


class ReminderService:
    def __init__(self, auth_service: AuthService, config: ReminderConfig):
        self.auth_service = auth_service
        self.default_timezone = config.timezone
        self.scheduler_timezone = ZoneInfo(config.timezone)
        self.days_of_week = self._parse_days_of_week(config.days_of_week)
        self.tasks = [
            ReminderTask(
                title="start_work",
                message=START_WORK_REMINDER_TEXT,
                settings_key="morning_time",
                default_time=parse_reminder_time(config.morning_time),
            ),
            ReminderTask(
                title="end_work",
                message=END_WORK_REMINDER_TEXT,
                settings_key="evening_time",
                default_time=parse_reminder_time(config.evening_time),
            ),
        ]
        self.scheduler = AsyncIOScheduler(timezone=self.scheduler_timezone)
        self._started = False
        self._sent_keys: set[tuple[int, str, str, str]] = set()

    def _parse_days_of_week(self, value: str) -> set[int]:
        mapping = {
            "mon": 0,
            "tue": 1,
            "wed": 2,
            "thu": 3,
            "fri": 4,
            "sat": 5,
            "sun": 6,
        }

        result = set()

        for day in value.split(","):
            normalized_day = day.strip().lower()
            if normalized_day in mapping:
                result.add(mapping[normalized_day])

        return result or {0, 1, 2, 3, 4}

    async def start(self, bot: Bot):
        if self._started:
            return

        self.scheduler.add_job(
            self.send_due_reminders,
            trigger=IntervalTrigger(minutes=1, timezone=self.scheduler_timezone),
            kwargs={"bot": bot},
            id="reminders:due-check",
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

    def _get_user_settings(self, user_id: int) -> dict[str, str]:
        return self.auth_service.get_notification_settings(
            user_id,
            self.tasks[0].default_time.strftime("%H:%M"),
            self.tasks[1].default_time.strftime("%H:%M"),
            self.default_timezone,
        )

    def _is_due(self, task: ReminderTask, settings: dict[str, str]) -> tuple[bool, datetime | None]:
        timezone_name = settings.get("timezone") or self.default_timezone

        try:
            timezone = ZoneInfo(timezone_name)
        except ZoneInfoNotFoundError:
            timezone = ZoneInfo(self.default_timezone)

        now = datetime.now(timezone).replace(second=0, microsecond=0)

        if now.weekday() not in self.days_of_week:
            return False, now

        raw_time = settings.get(task.settings_key) or task.default_time.strftime("%H:%M")

        try:
            trigger_time = parse_reminder_time(raw_time)
        except ValueError:
            trigger_time = task.default_time

        return now.time() == trigger_time, now

    async def send_due_reminders(self, bot: Bot):
        user_ids = self.auth_service.get_user_ids()

        if not user_ids:
            return

        for user_id in user_ids:
            settings = self._get_user_settings(user_id)

            for task in self.tasks:
                is_due, local_now = self._is_due(task, settings)

                if not is_due or local_now is None:
                    continue

                sent_key = (
                    user_id,
                    task.title,
                    local_now.strftime("%Y-%m-%d"),
                    local_now.strftime("%H:%M"),
                )

                if sent_key in self._sent_keys:
                    continue

                await self.send_reminder(bot, user_id, task)
                self._sent_keys.add(sent_key)

    async def send_reminder(self, bot: Bot, user_id: int, task: ReminderTask):
        try:
            await bot.send_message(
                chat_id=user_id,
                text=task.message,
                parse_mode="HTML",
            )
        except TelegramAPIError as e:
            print(f"Не удалось отправить напоминание user_id={user_id}: {e}")