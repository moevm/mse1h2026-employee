import logging
import os
import sys
import time
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from config import load_config
from constants.sheets_constants import (
    TG_ID_COLUMN,
    ROLE_COLUMN,
    MANAGER_IDS_COLUMN,
    STARTED_AT_COLUMN,
    ENDED_AT_COLUMN,
    OFFER_ID_COLUMN,
    TITLE_COLUMN,
    DESCRIPTION_COLUMN,
    LEAD_ID_COLUMN,
    AUTHOR_ID_COLUMN,
    STATUS_COLUMN,
    CREATED_AT_COLUMN,
    TASK_ID_COLUMN,
    EMPLOYEE_ID_COLUMN,
    UPDATED_AT_COLUMN,
    DEADLINE_COLUMN,
    BIND_REQUEST_ID_COLUMN,
    BIND_EMPLOYEE_ID_COLUMN,
    BIND_EMPLOYEE_ROLE_COLUMN,
    BIND_LEAD_ID_COLUMN,
    BIND_CREATED_AT_COLUMN,
    NOTIFICATION_MORNING_TIME_COLUMN,
    NOTIFICATION_EVENING_TIME_COLUMN,
    NOTIFICATION_TIMEZONE_COLUMN,
)
from services.accepted_tasks_service import AcceptedTasksService
from services.daily_reports_service import DailyReportsService
from services.google_sheets import GoogleSheetsClient

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")


def _resolve_creds_path(path: str) -> str:
    if not os.path.isabs(path):
        return os.path.join(os.path.dirname(__file__), "..", path)
    return path


def main():
    try:
        config = load_config()

        creds_path = _resolve_creds_path(config.sheets.credentials_path)
        if not os.path.exists(creds_path):
            logging.error(f"Файл {creds_path} не найден")
            sys.exit(1)

        if not config.sheets.sheet_id:
            logging.error("GOOGLE_SHEET_ID не задан")
            sys.exit(1)

        client = GoogleSheetsClient(
            credentials_path=creds_path,
            sheet_id=config.sheets.sheet_id,
        )

        roles_headers = [
            TG_ID_COLUMN,
            ROLE_COLUMN,
            MANAGER_IDS_COLUMN,
            NOTIFICATION_MORNING_TIME_COLUMN,
            NOTIFICATION_EVENING_TIME_COLUMN,
            NOTIFICATION_TIMEZONE_COLUMN,
        ]

        role_requests_headers = [TG_ID_COLUMN, ROLE_COLUMN]
        visits_headers = [TG_ID_COLUMN, STARTED_AT_COLUMN, ENDED_AT_COLUMN]

        task_requests_headers = [
            OFFER_ID_COLUMN,
            TITLE_COLUMN,
            DESCRIPTION_COLUMN,
            LEAD_ID_COLUMN,
            AUTHOR_ID_COLUMN,
            STATUS_COLUMN,
            CREATED_AT_COLUMN,
        ]

        tasks_headers = [
            TASK_ID_COLUMN,
            TITLE_COLUMN,
            DESCRIPTION_COLUMN,
            EMPLOYEE_ID_COLUMN,
            AUTHOR_ID_COLUMN,
            STATUS_COLUMN,
            CREATED_AT_COLUMN,
            UPDATED_AT_COLUMN,
            DEADLINE_COLUMN,
        ]

        reports_headers = [
            "ReportID",
            TASK_ID_COLUMN,
            EMPLOYEE_ID_COLUMN,
            "Text",
            CREATED_AT_COLUMN,
            "ManagerFeedback",
        ]

        manager_bind_headers = [
            BIND_REQUEST_ID_COLUMN,
            BIND_EMPLOYEE_ID_COLUMN,
            BIND_EMPLOYEE_ROLE_COLUMN,
            BIND_LEAD_ID_COLUMN,
            BIND_CREATED_AT_COLUMN,
        ]

        sheets_to_init = [
            (config.sheets.roles_sheet_name, roles_headers),
            (config.sheets.task_requests_sheet_name, task_requests_headers),
            (config.sheets.tasks_sheet_name, tasks_headers),
            (config.sheets.daily_reports_sheet_name, DailyReportsService.HEADERS),
            (config.sheets.role_requests_sheet_name, role_requests_headers),
            (config.sheets.manager_bind_requests_sheet_name, manager_bind_headers),
            (config.sheets.visits_sheet_name, visits_headers),
            (config.sheets.reports_sheet_name, reports_headers),
            (config.sheets.accepted_tasks_sheet_name, AcceptedTasksService.HEADERS),
            (config.sheets.banned_users_sheet_name, ["Telegram ID", "Reason", "CreatedAt"]),
            
        ]

        for sheet_name, headers in sheets_to_init:
            client.ensure_headers(sheet_name, headers)
            logging.info(f"Лист '{sheet_name}' готов (колонок: {len(headers)})")
            time.sleep(1)

        default_titles = {"Лист1"}

        required_sheet_names = {
            config.sheets.roles_sheet_name,
            config.sheets.role_requests_sheet_name,
            config.sheets.visits_sheet_name,
            config.sheets.task_requests_sheet_name,
            config.sheets.tasks_sheet_name,
            config.sheets.reports_sheet_name,
            config.sheets.daily_reports_sheet_name,
            config.sheets.accepted_tasks_sheet_name,
            config.sheets.manager_bind_requests_sheet_name,
            config.sheets.banned_users_sheet_name,
        }

        worksheets = client.spreadsheet.worksheets()
        if len(worksheets) > 1:
            for ws in worksheets:
                if ws.title in default_titles and ws.title not in required_sheet_names:
                    values = ws.get_all_values()
                    has_data = any(any(cell.strip() for cell in row) for row in values)

                    if not has_data:
                        client.spreadsheet.del_worksheet(ws)
                        logging.info(f"Удалён дефолтный лист '{ws.title}'")
                    break

        logging.info("Инициализация таблиц завершена.")

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
