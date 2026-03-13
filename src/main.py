import asyncio
import logging


from datetime import time
from aiogram import Bot, Dispatcher
from config import load_config
from handlers.auth import setup_auth_router
from handlers.start import router as start_router
from services.auth_service import AuthService
from services.google_sheets import GoogleSheetsClient
from services.reminder_service import ReminderService



async def main():
    logging.basicConfig(level=logging.INFO)

    config = load_config()

    if not config.bot.token:
        raise ValueError("BOT_TOKEN не найден в .env")

    if not config.sheets.sheet_id:
        raise ValueError("GOOGLE_SHEET_ID не найден в .env")

    bot = Bot(token=config.bot.token)
    dp = Dispatcher()

    sheets_client = GoogleSheetsClient(
        credentials_path=config.sheets.credentials_path,
        sheet_id=config.sheets.sheet_id,
    )

    auth_service = AuthService(
        sheets_client=sheets_client,
        roles_sheet_name=config.sheets.roles_sheet_name,
    )

    reminder_service = ReminderService(
        auth_service=auth_service,
        config=config.reminders,
    )

    dp.include_router(start_router)
    dp.include_router(setup_auth_router(auth_service))

    await reminder_service.start(bot)

    try:
        await dp.start_polling(bot)
    finally:
        await reminder_service.stop()

    dp.include_router(start_router)
    dp.include_router(setup_auth_router(auth_service))

    await dp.start_polling(bot)



if __name__ == "__main__":
    asyncio.run(main())