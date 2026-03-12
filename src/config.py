import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
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