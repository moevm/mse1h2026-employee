import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass
class BotConfig:
    token: str


@dataclass
class SheetsConfig:
    credentials_path: str
    sheet_id: str
    roles_sheet_name: str
    role_requests_sheet_name: str
    visits_sheet_name: str
    task_requests_sheet_name: str
    tasks_sheet_name: str
    reports_sheet_name: str
    daily_reports_sheet_name: str
    accepted_tasks_sheet_name: str
    manager_bind_requests_sheet_name: str
    banned_users_sheet_name: str


@dataclass
class ReminderConfig:
    timezone: str
    days_of_week: str
    morning_time: str
    evening_time: str


@dataclass
class Config:
    bot: BotConfig
    sheets: SheetsConfig
    reminders: ReminderConfig


def load_config():
    bot = BotConfig(token=os.getenv("BOT_TOKEN", ""))
    sheets = SheetsConfig(
        credentials_path=os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"),
        sheet_id=os.getenv("GOOGLE_SHEET_ID", ""),
        roles_sheet_name=os.getenv("ROLES_SHEET_NAME", "Роли"),
        role_requests_sheet_name=os.getenv("ROLE_REQUESTS_SHEET_NAME", "Запросы ролей"),
        visits_sheet_name=os.getenv("VISITS_SHEET_NAME", "Посещения"),
        task_requests_sheet_name=os.getenv("TASK_REQUESTS_SHEET_NAME", "Запросы задач"),
        tasks_sheet_name=os.getenv("TASKS_SHEET_NAME", "Задачи"),
        reports_sheet_name=os.getenv("REPORTS_SHEET_NAME", "Отчеты"),
        daily_reports_sheet_name=os.getenv(
            "DAILY_REPORTS_SHEET_NAME", "Ежедневные отчеты"
        ),
        accepted_tasks_sheet_name=os.getenv(
            "ACCEPTED_TASKS_SHEET_NAME", "Принятые задачи"
        ),
        manager_bind_requests_sheet_name=os.getenv(
            "MANAGER_BIND_REQUESTS_SHEET_NAME", "Запросы руководителей"
        ),
        banned_users_sheet_name=os.getenv("BANNED_USERS_SHEET_NAME", "Заблокированные"),
    )
    reminders = ReminderConfig(
        timezone=os.getenv("REMINDERS_TIMEZONE", "Europe/Moscow"),
        days_of_week=os.getenv("REMINDERS_DAYS_OF_WEEK", "mon,tue,wed,thu,fri"),
        morning_time=os.getenv("REMINDER_MORNING_TIME", "08:50"),
        evening_time=os.getenv("REMINDER_EVENING_TIME", "16:50"),
    )
    return Config(bot, sheets, reminders)
