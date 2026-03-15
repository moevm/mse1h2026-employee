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
    bot=BotConfig(token=os.getenv("BOT_TOKEN", ""))
    sheets=SheetsConfig(
        credentials_path=os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"),
        sheet_id=os.getenv("GOOGLE_SHEET_ID", ""),
        roles_sheet_name=os.getenv("ROLES_SHEET_NAME", "Роли"),
        role_requests_sheet_name=os.getenv("ROLE_REQUESTS_SHEET_NAME", "Запросы ролей"),
        visits_sheet_name=os.getenv("VISITS_SHEET_NAME", "Посещения"),
        )
    reminders=ReminderConfig(
            timezone=os.getenv("REMINDERS_TIMEZONE", "Europe/Moscow"),
            days_of_week=os.getenv("REMINDERS_DAYS_OF_WEEK", "mon,tue,wed,thu,fri"),
            morning_time=os.getenv("REMINDER_MORNING_TIME", "08:50"),
            evening_time=os.getenv("REMINDER_EVENING_TIME", "16:50"),
        )
    return Config(bot, sheets, reminders)
  
class TgBotConfig:
    token: str

@dataclass
class GoogleSheetsConfig:
    sheet_id: str
    credentials_path: str
    roles_sheet_name: str = "Роли"
    role_requests_sheet_name: str = "Запросы ролей"
    visits_sheet_name: str = "Посещения"

@dataclass
class Config:
    bot: TgBotConfig
    sheets: GoogleSheetsConfig

def load_config():
    bot = TgBotConfig(token=os.getenv("BOT_TOKEN", ""))
    sheets = GoogleSheetsConfig(
            sheet_id=os.getenv("GOOGLE_SHEET_ID", ""),
            credentials_path=os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json"),
            roles_sheet_name=os.getenv("ROLES_SHEET_NAME", "Роли"),
            role_requests_sheet_name=os.getenv("ROLE_REQUESTS_SHEET_NAME", "Запросы ролей"),
            visits_sheet_name=os.getenv("VISITS_SHEET_NAME", "Посещения"),
        )
    return Config(bot, sheets)

