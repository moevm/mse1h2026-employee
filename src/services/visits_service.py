from datetime import datetime
from zoneinfo import ZoneInfo

from constants.sheets_constants import (
    TG_ID_COLUMN,
    ENDED_AT_COLUMN,
)
from services.google_sheets import GoogleSheetsClient


class VisitsService:
    def __init__(
        self,
        sheets_client: GoogleSheetsClient,
        visits_sheet_name: str,
        timezone: str = "Europe/Moscow",
    ):
        self.sheets_client = sheets_client
        self.visits_sheet_name = visits_sheet_name
        self.timezone = timezone

    def _now_str(self) -> str:
        return datetime.now(ZoneInfo(self.timezone)).strftime("%Y-%m-%d %H:%M:%S")

    def has_open_visit(self, tg_id: int) -> bool:
        records = self.sheets_client.get_all_records(self.visits_sheet_name)

        for row in reversed(records):
            if str(row.get(TG_ID_COLUMN)) == str(tg_id) and not row.get(ENDED_AT_COLUMN):
                return True
        return False

    def start_workday(self, tg_id: int) -> bool:
        if self.has_open_visit(tg_id):
            return False

        self.sheets_client.append_row(
            self.visits_sheet_name,
            [tg_id, self._now_str(), ""],
        )
        return True

    def finish_workday(self, tg_id: int) -> bool:
        worksheet = self.sheets_client.get_worksheet(self.visits_sheet_name)
        records = worksheet.get_all_records()
        headers = worksheet.row_values(1)

        ended_at_col = headers.index(ENDED_AT_COLUMN) + 1

        for i in range(len(records) - 1, -1, -1):
            row = records[i]
            if str(row.get(TG_ID_COLUMN)) == str(tg_id) and not row.get(ENDED_AT_COLUMN):
                sheet_row_index = i + 2
                worksheet.update_cell(sheet_row_index, ended_at_col, self._now_str())
                return True

        return False