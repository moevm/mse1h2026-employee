from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from constants.sheets_constants import (
    TG_ID_COLUMN,
    STARTED_AT_COLUMN,
    ENDED_AT_COLUMN,
)
from services.google_sheets import GoogleSheetsClient


@dataclass
class VisitRecord:
    row_index: int
    tg_id: int | None
    started_at: str
    ended_at: str


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

    @staticmethod
    def _normalize_header(value: str) -> str:
        return re.sub(r"[^a-z0-9а-яё]", "", str(value).strip().lower())

    @staticmethod
    def _parse_int(value: str) -> int | None:
        digits = re.sub(r"\D", "", str(value).strip())
        return int(digits) if digits else None

    @staticmethod
    def _date_part(value: str) -> str:
        value = str(value).strip()
        match = re.search(r"\d{4}-\d{2}-\d{2}", value)
        if match:
            return match.group(0)
        return value

    @staticmethod
    def _zoneinfo(timezone: str, fallback: str = "Europe/Moscow") -> ZoneInfo:
        try:
            return ZoneInfo(timezone)
        except ZoneInfoNotFoundError:
            return ZoneInfo(fallback)

    def _parse_datetime(self, value: str, timezone: str | None = None) -> datetime | None:
        raw_value = str(value or "").strip()
        if not raw_value:
            return None

        normalized = raw_value.replace("Z", "+00:00")
        parsed: datetime | None = None

        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M:%S", "%d.%m.%Y %H:%M"):
                try:
                    parsed = datetime.strptime(raw_value, fmt)
                    break
                except ValueError:
                    continue

        if parsed is None:
            return None

        zone = self._zoneinfo(timezone or self.timezone, self.timezone)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=zone)
        return parsed.astimezone(zone)

    def find_column(self, headers: list[str], *aliases: str) -> int | None:
        normalized_headers = [self._normalize_header(header) for header in headers]
        normalized_aliases = {self._normalize_header(alias) for alias in aliases}

        for index, header in enumerate(normalized_headers):
            if header in normalized_aliases:
                return index
        return None

    def read_rows(self) -> tuple[list[str], list[list[str]]]:
        values = self.sheets_client.get_all_values(self.visits_sheet_name)
        if not values:
            return [], []
        return values[0], values[1:]

    def build_visit(self, headers: list[str], row: list[str], row_index: int) -> VisitRecord | None:
        tg_id_index = self.find_column(headers, TG_ID_COLUMN, "TelegramID", "EmployeeID")
        started_at_index = self.find_column(headers, STARTED_AT_COLUMN, "Start", "Started", "StartTime")
        ended_at_index = self.find_column(headers, ENDED_AT_COLUMN, "End", "Ended", "EndTime")

        if tg_id_index is None or started_at_index is None:
            return None

        def value_at(index: int | None) -> str:
            if index is None or index >= len(row):
                return ""
            return str(row[index]).strip()

        started_at = value_at(started_at_index)
        if not started_at:
            return None

        return VisitRecord(
            row_index=row_index,
            tg_id=self._parse_int(value_at(tg_id_index)),
            started_at=started_at,
            ended_at=value_at(ended_at_index),
        )

    def get_all_visits(self) -> list[VisitRecord]:
        headers, rows = self.read_rows()
        if not headers:
            return []

        visits: list[VisitRecord] = []
        for index, row in enumerate(rows, start=2):
            visit = self.build_visit(headers, row, index)
            if visit is not None:
                visits.append(visit)
        return visits

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

    def list_visits_for_employee_between(self, employee_id: int, start_date: date, end_date: date) -> list[VisitRecord]:
        result: list[VisitRecord] = []
        for visit in self.get_all_visits():
            if visit.tg_id != employee_id:
                continue
            started_at = self._parse_datetime(visit.started_at)
            if started_at is None:
                continue
            started_date = started_at.date()
            if start_date <= started_date <= end_date:
                result.append(visit)
        return result

    def sum_worked_hours_for_employee_between(self, employee_id: int, start_date: date, end_date: date) -> float:
        total_seconds = 0.0
        for visit in self.list_visits_for_employee_between(employee_id, start_date, end_date):
            started_at = self._parse_datetime(visit.started_at)
            ended_at = self._parse_datetime(visit.ended_at)
            if started_at is None or ended_at is None or ended_at <= started_at:
                continue
            total_seconds += (ended_at - started_at).total_seconds()
        return round(total_seconds / 3600, 2)

