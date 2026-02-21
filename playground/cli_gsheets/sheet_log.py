import sys
import os
from datetime import datetime
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials


load_dotenv()

def get_table_by_id(client, table_id): 
    return client.open_by_key(table_id)

def get_google_client():
    """Авторизация и получение клиента gspread."""
    service_account_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(service_account_file, scopes=scopes)
    return gspread.authorize(creds)

def insert_one(table, title: str, data: list, index: int = 1):
    """Вставка данных в конкретный лист."""
    worksheet = table.worksheet(title)
    worksheet.insert_row(data, index=index)


def main():
    if len(sys.argv) < 2:
        print("Использование: python main.py 'Текст сообщения'")
        return

    message = " ".join(sys.argv[1:])
    table_id = os.getenv('GOOGLE_SHEET_ID')
    worksheet_title = os.getenv('WORKSHEET_TITLE', 'Лист1')

    try:
        client = get_google_client()
        table = client.open_by_key(table_id) 
        
        insert_one(table, worksheet_title, [message], index=1)
        
        print(f"Запись '{[message]}' добавлена в лист '{worksheet_title}'")

    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()