from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re

from services.google_sheets import GoogleSheetsClient
from services.reports_service import ReportRecord
from services.tasks_service import TaskRecord


@dataclass
class AcceptedTaskRecord:
    row_index: int
    report_id: str
    employee_id: int | None
    date_value: str
    task_title: str
    description: str
    problems: str
    status: str
    manager_feedback: str


class AcceptedTasksService:
    HEADERS = [
        "ReportID",
        "TelegramID",
        "Date",
        "TasksDone",
        "Description",
        "Problems",
        "Status",
        "ManagerFeedback",
        "Deadline",
        "ClosedAt"
    ]
    
    def __init__(self, sheets_client: GoogleSheetsClient, accepted_tasks_sheet_name: str):
        self.sheets_client = sheets_client
        self.accepted_tasks_sheet_name = accepted_tasks_sheet_name

    @staticmethod
    def _now_str() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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

    def find_column(self, headers: list[str], *aliases: str) -> int | None:
        normalized_headers = [self._normalize_header(header) for header in headers]
        normalized_aliases = {self._normalize_header(alias) for alias in aliases}

        for index, header in enumerate(normalized_headers):
            if header in normalized_aliases:
                return index
        return None

    def read_rows(self) -> tuple[list[str], list[list[str]]]:
        values = self.sheets_client.get_all_values(self.accepted_tasks_sheet_name)
        if not values:
            return [], []
        return values[0], values[1:]

    def build_record(self, headers: list[str], row: list[str], row_index: int) -> AcceptedTaskRecord | None:
        report_id_index = self.find_column(headers, "ReportID", "ReportId", "report_id")
        employee_id_index = self.find_column(headers, "TelegramID", "Telegram ID", "EmployeeID", "employee_id")
        date_index = self.find_column(headers, "Date", "CreatedAt", "created_at")
        task_title_index = self.find_column(headers, "TasksDone", "TaskTitle", "Title", "Название")
        description_index = self.find_column(headers, "Description", "Text", "ReportText")
        problems_index = self.find_column(headers, "Problems", "Проблемы")
        status_index = self.find_column(headers, "Status")
        feedback_index = self.find_column(headers, "ManagerFeedback", "Комментарий руководителя")

        if report_id_index is None or employee_id_index is None:
            return None

        def value_at(index: int | None) -> str:
            if index is None or index >= len(row):
                return ""
            return str(row[index]).strip()

        report_id = value_at(report_id_index)
        if not report_id:
            return None

        return AcceptedTaskRecord(
            row_index=row_index,
            report_id=report_id,
            employee_id=self._parse_int(value_at(employee_id_index)),
            date_value=value_at(date_index),
            task_title=value_at(task_title_index),
            description=value_at(description_index),
            problems=value_at(problems_index),
            status=value_at(status_index),
            manager_feedback=value_at(feedback_index),
        )

    def get_all_records(self) -> list[AcceptedTaskRecord]:
        headers, rows = self.read_rows()
        if not headers:
            return []

        records: list[AcceptedTaskRecord] = []
        for index, row in enumerate(rows, start=2):
            record = self.build_record(headers, row, index)
            if record is not None:
                records.append(record)
        return records

    def list_task_titles_for_employee_on_date(self, employee_id: int, report_date: str) -> list[str]:
        titles: list[str] = []
        normalized_date = self._date_part(report_date)

        for record in self.get_all_records():
            if record.employee_id != employee_id:
                continue
            if self._date_part(record.date_value) != normalized_date:
                continue
            title = (record.task_title or "").strip()
            if title and title not in titles:
                titles.append(title)

        return titles

    def create_from_report(
        self,
        report: ReportRecord,
        task: TaskRecord,
        manager_feedback: str = "",
    ):
        raw = report.raw_fields or {}

        report_id = raw.get("ReportID") or raw.get("ReportId") or report.report_id
        telegram_id = raw.get("TelegramID") or task.employee_id or report.employee_id or ""
        date_value = raw.get("Date") or report.created_at or self._now_str()
        tasks_done = raw.get("TasksDone") or task.title
        description = raw.get("Description") or report.text
        problems = raw.get("Problems") or ""
        status = "accepted"
        feedback = manager_feedback if manager_feedback else raw.get("ManagerFeedback", "")

        self.sheets_client.append_row(
            self.accepted_tasks_sheet_name,
            [report_id, telegram_id, date_value, tasks_done, description, problems, status, feedback],
        )
