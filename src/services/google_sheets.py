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

    def append_row(self, sheet_name: str, values: list[Any]):
        worksheet = self.get_worksheet(sheet_name)
        worksheet.append_row(
            [self._normalize(v) for v in values],
            value_input_option="USER_ENTERED",
        )


    def append_rows(self, sheet_name: str, rows: list[list[Any]]):
        if not rows:
            return
        worksheet = self.get_worksheet(sheet_name)
        worksheet.append_rows(
            [[self._normalize(v) for v in row] for row in rows],
            value_input_option="USER_ENTERED",
        )

    def get_all_values(self, sheet_name: str):
        worksheet = self.get_worksheet(sheet_name)
        return worksheet.get_all_values()

    def delete_row(self, sheet_name: str, row_index: int):
        worksheet = self.get_worksheet(sheet_name)
        worksheet.delete_rows(row_index)


    @staticmethod
    def _build_contiguous_ranges(row_indices: list[int]) -> list[tuple[int, int]]:
        unique_rows = sorted({int(row) for row in row_indices if int(row) > 0})
        if not unique_rows:
            return []

        ranges: list[tuple[int, int]] = []
        start = previous = unique_rows[0]
        for row in unique_rows[1:]:
            if row == previous + 1:
                previous = row
                continue
            ranges.append((start, previous))
            start = previous = row
        ranges.append((start, previous))
        return ranges

    def delete_rows_batch(self, sheet_name: str, row_indices: list[int]) -> int:
        ranges = [
            row_range
            for row_range in self._build_contiguous_ranges(row_indices)
            if row_range[0] >= 2
        ]
        if not ranges:
            return 0

        worksheet = self.get_worksheet(sheet_name)
        requests = []
        for start_row, end_row in sorted(ranges, key=lambda item: item[0], reverse=True):
            requests.append(
                {
                    "deleteDimension": {
                        "range": {
                            "sheetId": worksheet.id,
                            "dimension": "ROWS",
                            "startIndex": start_row - 1,
                            "endIndex": end_row,
                        }
                    }
                }
            )

        self.spreadsheet.batch_update({"requests": requests})
        return sum(end_row - start_row + 1 for start_row, end_row in ranges)

    def update_cell(self, sheet_name: str, row: int, col: int, value: str) -> None:
        worksheet = self.spreadsheet.worksheet(sheet_name)
        worksheet.update_cell(row, col, value)