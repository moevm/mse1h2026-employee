import logging
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from config import load_config
from services.google_sheets import GoogleSheetsClient

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s"
)


def main():
    try:
        config = load_config()

        creds_path = config.sheets.credentials_path
        if not os.path.isabs(creds_path):
            creds_path = os.path.join(os.path.dirname(__file__), "..", creds_path)

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

        records = client.get_all_records(config.sheets.roles_sheet_name)
        has_superuser = any(
            str(row.get("Role", "")).strip().lower() == "superuser" for row in records
        )

        if has_superuser:
            logging.info("Суперпользователь уже существует.")
            return

        print("\nСписок суперпользователей пуст.")
        tg_id = input("Введите ваш Telegram ID для назначения роли superuser: ").strip()

        if not tg_id.isdigit():
            logging.error("ID должен содержать только цифры.")
            sys.exit(1)

        client.append_row(config.sheets.roles_sheet_name, [tg_id, "superuser", ""])
        logging.info(f"Пользователь {tg_id} успешно добавлен как superuser.")

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
