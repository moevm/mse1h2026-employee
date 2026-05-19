from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
import uuid
from zoneinfo import ZoneInfo

from constants.sheets_constants import (
    COMPLETED_TASKS_COUNT_COLUMN,
    COMPLETED_TASKS_TITLES_COLUMN,
    DAILY_REPORT_DATE_COLUMN,
    DAILY_REPORT_ID_COLUMN,
    EMPLOYEE_ID_COLUMN,
    IN_PROCESS_TASKS_COUNT_COLUMN,
    IN_PROCESS_TASKS_TITLES_COLUMN,
    PROBLEMS_COLUMN,
    WORK_DONE_COLUMN,
    CREATED_AT_COLUMN,
)
from services.google_sheets import GoogleSheetsClient


@dataclass
class DailyReportRecord:
    row_index: int
    report_id: str
    employee_id: int | None
    report_date: str
    work_done: str
    problems: str
    completed_tasks_count: int
    completed_tasks_titles: str
    in_process_tasks_count: int
    in_process_tasks_titles: str
    created_at: str
    raw_fields: dict[str, str]


class DailyReportsService:
    HEADERS = [
        DAILY_REPORT_ID_COLUMN,
        EMPLOYEE_ID_COLUMN,
        DAILY_REPORT_DATE_COLUMN,
        WORK_DONE_COLUMN,
        PROBLEMS_COLUMN,
        COMPLETED_TASKS_COUNT_COLUMN,
        COMPLETED_TASKS_TITLES_COLUMN,
        IN_PROCESS_TASKS_COUNT_COLUMN,
        IN_PROCESS_TASKS_TITLES_COLUMN,
        CREATED_AT_COLUMN,
    ]

    def __init__(self, sheets_client: GoogleSheetsClient, sheet_name: str, timezone: str = "Europe/Moscow"):
        self.sheets_client = sheets_client
        self.sheet_name = sheet_name
        self.timezone = timezone

    @staticmethod
    def _normalize_header(value: str) -> str:
        return re.sub(r"[^a-z0-9а-яё]", "", str(value).strip().lower())

    @staticmethod
    def _parse_int(value: str) -> int | None:
        digits = re.sub(r"\D", "", str(value).strip())
        return int(digits) if digits else None

    @staticmethod
    def _parse_count(value: str) -> int:
        digits = re.sub(r"\D", "", str(value).strip())
        return int(digits) if digits else 0

    @staticmethod
    def _date_part(value: str) -> str:
        value = str(value).strip()
        match = re.search(r"\d{4}-\d{2}-\d{2}", value)
        if match:
            return match.group(0)
        return value

    def _now_str(self) -> str:
        return datetime.now(ZoneInfo(self.timezone)).strftime("%Y-%m-%d %H:%M:%S")

    def today_str(self) -> str:
        return datetime.now(ZoneInfo(self.timezone)).strftime("%Y-%m-%d")

    def ensure_sheet(self):
        return self.sheets_client.ensure_headers(self.sheet_name, self.HEADERS)

    def find_column(self, headers: list[str], *aliases: str) -> int | None:
        normalized_headers = [self._normalize_header(header) for header in headers]
        normalized_aliases = {self._normalize_header(alias) for alias in aliases}

        for index, header in enumerate(normalized_headers):
            if header in normalized_aliases:
                return index
        return None

    def read_rows(self) -> tuple[list[str], list[list[str]]]:
        self.ensure_sheet()
        values = self.sheets_client.get_all_values(self.sheet_name)
        if not values:
            return [], []
        return values[0], values[1:]

    def build_report(self, headers: list[str], row: list[str], row_index: int) -> DailyReportRecord | None:
        report_id_index = self.find_column(headers, DAILY_REPORT_ID_COLUMN, "ReportID", "ReportId")
        employee_id_index = self.find_column(headers, EMPLOYEE_ID_COLUMN, "TelegramID", "Telegram ID")
        report_date_index = self.find_column(headers, DAILY_REPORT_DATE_COLUMN, "Date", "Дата")
        work_done_index = self.find_column(headers, WORK_DONE_COLUMN, "Work", "Что сделано", "Какая работа была проделана")
        problems_index = self.find_column(headers, PROBLEMS_COLUMN, "Проблемы")
        completed_count_index = self.find_column(headers, COMPLETED_TASKS_COUNT_COLUMN)
        completed_titles_index = self.find_column(headers, COMPLETED_TASKS_TITLES_COLUMN)
        in_process_count_index = self.find_column(headers, IN_PROCESS_TASKS_COUNT_COLUMN)
        in_process_titles_index = self.find_column(headers, IN_PROCESS_TASKS_TITLES_COLUMN)
        created_at_index = self.find_column(headers, CREATED_AT_COLUMN, "Created", "CreatedAt")

        if report_id_index is None or employee_id_index is None or report_date_index is None:
            return None

        def value_at(index: int | None) -> str:
            if index is None or index >= len(row):
                return ""
            return str(row[index]).strip()

        report_id = value_at(report_id_index)
        if not report_id:
            return None

        raw_fields: dict[str, str] = {}
        for index, header in enumerate(headers):
            raw_fields[str(header).strip()] = str(row[index]).strip() if index < len(row) else ""

        return DailyReportRecord(
            row_index=row_index,
            report_id=report_id,
            employee_id=self._parse_int(value_at(employee_id_index)),
            report_date=self._date_part(value_at(report_date_index)),
            work_done=value_at(work_done_index),
            problems=value_at(problems_index),
            completed_tasks_count=self._parse_count(value_at(completed_count_index)),
            completed_tasks_titles=value_at(completed_titles_index),
            in_process_tasks_count=self._parse_count(value_at(in_process_count_index)),
            in_process_tasks_titles=value_at(in_process_titles_index),
            created_at=value_at(created_at_index),
            raw_fields=raw_fields,
        )

    def get_all_reports(self) -> list[DailyReportRecord]:
        headers, rows = self.read_rows()
        if not headers:
            return []

        reports: list[DailyReportRecord] = []
        for index, row in enumerate(rows, start=2):
            report = self.build_report(headers, row, index)
            if report is not None:
                reports.append(report)
        return reports

    def get_report_for_employee_date(self, employee_id: int, report_date: str) -> DailyReportRecord | None:
        normalized_employee_id = str(employee_id).strip()
        normalized_date = self._date_part(report_date)

        for report in self.get_all_reports():
            if str(report.employee_id) == normalized_employee_id and report.report_date == normalized_date:
                return report
        return None

    def create_or_update_report(
        self,
        employee_id: int,
        report_date: str,
        work_done: str,
        problems: str,
        completed_tasks_titles: list[str],
        in_process_tasks_titles: list[str],
    ) -> tuple[str, bool]:
        self.ensure_sheet()
        headers, _ = self.read_rows()
        existing_report = self.get_report_for_employee_date(employee_id, report_date)
        report_id = existing_report.report_id if existing_report else uuid.uuid4().hex
        created_at = self._now_str()

        completed_titles_text = "\n".join(completed_tasks_titles)
        in_process_titles_text = "\n".join(in_process_tasks_titles)

        values_by_header = {
            DAILY_REPORT_ID_COLUMN: report_id,
            EMPLOYEE_ID_COLUMN: str(employee_id),
            DAILY_REPORT_DATE_COLUMN: self._date_part(report_date),
            WORK_DONE_COLUMN: work_done,
            PROBLEMS_COLUMN: problems,
            COMPLETED_TASKS_COUNT_COLUMN: len(completed_tasks_titles),
            COMPLETED_TASKS_TITLES_COLUMN: completed_titles_text,
            IN_PROCESS_TASKS_COUNT_COLUMN: len(in_process_tasks_titles),
            IN_PROCESS_TASKS_TITLES_COLUMN: in_process_titles_text,
            CREATED_AT_COLUMN: created_at,
        }

        if existing_report is None:
            self.sheets_client.append_row(
                self.sheet_name,
                [values_by_header.get(header, "") for header in self.HEADERS],
            )
            return report_id, False

        for header, value in values_by_header.items():
            col_index = self.find_column(headers, header)
            if col_index is None:
                continue
            self.sheets_client.update_cell(
                self.sheet_name,
                existing_report.row_index,
                col_index + 1,
                str(value),
            )
        return report_id, True

    def list_reports_for_date(
        self,
        report_date: str,
        employee_ids: list[int] | set[int] | tuple[int, ...] | None = None,
    ) -> list[DailyReportRecord]:
        normalized_date = self._date_part(report_date)
        allowed_ids = {int(value) for value in employee_ids} if employee_ids is not None else None

        reports = [report for report in self.get_all_reports() if report.report_date == normalized_date]
        if allowed_ids is not None:
            reports = [report for report in reports if report.employee_id in allowed_ids]

        return list(reversed(reports))
