from __future__ import annotations

from typing import Any

import gspread
from google.oauth2.service_account import Credentials


class GoogleSheetsClient:
    def __init__(self, credentials_path: str, sheet_id: str):
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=scopes,
        )

        self.client = gspread.authorize(credentials)
        self.spreadsheet = self.client.open_by_key(sheet_id)

    def get_worksheet(self, sheet_name: str):
        return self.spreadsheet.worksheet(sheet_name)

    @staticmethod
    def _normalize(value: Any):
        return str(value).strip()

    def get_all_records(self, sheet_name: str):
        worksheet = self.get_worksheet(sheet_name)
        return worksheet.get_all_records()

    