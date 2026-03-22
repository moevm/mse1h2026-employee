import asyncio
import logging

from aiogram import Bot, Dispatcher
from config import load_config

from handlers.auth import setup_auth_router
from handlers.common import setup_common_router
from handlers.employee import setup_employee_router
from handlers.intern import setup_intern_router
from handlers.lead import setup_lead_router
from handlers.start import setup_start_router
from handlers.superuser import setup_superuser_router
from handlers.task_request import setup_task_request_router

from services.auth_service import AuthService
from services.google_sheets import GoogleSheetsClient
from services.reminder_service import ReminderService
from services.role_request_service import RoleRequestService
from services.task_request_service import TaskRequestService
from services.tasks_service import TasksService


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

    role_request_service = RoleRequestService(
        sheets_client=sheets_client,
        role_requests_sheet_name=config.sheets.role_requests_sheet_name,
    )

    task_request_service = TaskRequestService(
        sheets_client=sheets_client,
        task_requests_sheet_name=config.sheets.task_requests_sheet_name,
    )

    tasks_service = TasksService(
        sheets_client=sheets_client,
        tasks_sheet_name=config.sheets.tasks_sheet_name,
    )

    reminder_service = ReminderService(
        auth_service=auth_service,
        config=config.reminders,
    )

    dp.include_router(setup_start_router(auth_service))
    dp.include_router(setup_auth_router(auth_service, role_request_service))
    dp.include_router(setup_task_request_router(auth_service, task_request_service))
    dp.include_router(setup_common_router(auth_service))
    dp.include_router(setup_superuser_router(auth_service, role_request_service))
    dp.include_router(setup_lead_router(auth_service, tasks_service))
    dp.include_router(setup_employee_router(auth_service))
    dp.include_router(setup_intern_router(auth_service))

    await reminder_service.start(bot)
    try:
        await dp.start_polling(bot)
    finally:
        await reminder_service.stop()


if __name__ == "__main__":
    asyncio.run(main())