from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import re

from constants.sheets_constants import DEADLINE_COLUMN
from services.google_sheets import GoogleSheetsClient
from services.reports_service import ReportRecord
from services.tasks_service import TaskRecord


CLOSED_AT_COLUMN = "ClosedAt"
ASSIGNED_AT_COLUMN = "AssignedAt"


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
    deadline: str = ""
    closed_at: str = ""
    assigned_at: str = ""


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
        DEADLINE_COLUMN,
        CLOSED_AT_COLUMN,
        ASSIGNED_AT_COLUMN,
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

    @classmethod
    def _parse_date(cls, value: str) -> date | None:
        value = cls._date_part(value)
        if not value:
            return None
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            return None

    def ensure_sheet(self):
        if hasattr(self.sheets_client, "ensure_headers"):
            return self.sheets_client.ensure_headers(self.accepted_tasks_sheet_name, self.HEADERS)
        return None

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
        deadline_index = self.find_column(headers, DEADLINE_COLUMN, "Дедлайн")
        closed_at_index = self.find_column(headers, CLOSED_AT_COLUMN, "AcceptedAt", "FinishedAt", "Closed", "ClosedDate", "Дата закрытия")
        assigned_at_index = self.find_column(headers, ASSIGNED_AT_COLUMN, "AssignedDate", "Assigned", "Дата назначения")

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
            deadline=value_at(deadline_index),
            closed_at=value_at(closed_at_index),
            assigned_at=value_at(assigned_at_index),
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

    @staticmethod
    def _is_accepted_status(status: str) -> bool:
        normalized_status = (status or "accepted").strip().lower()
        return normalized_status in {"accepted", "closed", "done", "finished"}

    @classmethod
    def _closed_date(cls, record: AcceptedTaskRecord) -> date | None:
        return cls._parse_date(record.closed_at or record.date_value)

    def list_closed_tasks_for_employee_between(self, employee_id: int, start_date: date, end_date: date) -> list[AcceptedTaskRecord]:
        result: list[AcceptedTaskRecord] = []
        for record in self.get_all_records():
            if record.employee_id != employee_id:
                continue
            if not self._is_accepted_status(record.status):
                continue
            closed_date = self._closed_date(record)
            if closed_date is None:
                continue
            if start_date <= closed_date <= end_date:
                result.append(record)
        return result

    def count_closed_tasks_for_employee_between(self, employee_id: int, start_date: date, end_date: date) -> int:
        return len(self.list_closed_tasks_for_employee_between(employee_id, start_date, end_date))

    def list_closed_overdue_tasks_for_employee_between(self, employee_id: int, start_date: date, end_date: date) -> list[AcceptedTaskRecord]:
        result: list[AcceptedTaskRecord] = []
        for record in self.get_all_records():
            if record.employee_id != employee_id:
                continue
            if not self._is_accepted_status(record.status):
                continue
            closed_date = self._closed_date(record)
            deadline = self._parse_date(record.deadline)
            if closed_date is None or deadline is None:
                continue
            if start_date <= deadline <= end_date and closed_date > deadline:
                result.append(record)
        return result

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
        closed_at = self._now_str()

        report_id = raw.get("ReportID") or raw.get("ReportId") or report.report_id
        telegram_id = raw.get("TelegramID") or task.employee_id or report.employee_id or ""
        date_value = raw.get("Date") or report.created_at or closed_at
        tasks_done = raw.get("TasksDone") or task.title
        description = raw.get("Description") or report.text or task.description
        problems = raw.get("Problems") or ""
        status = "accepted"
        feedback = manager_feedback if manager_feedback else raw.get("ManagerFeedback", "")
        deadline = raw.get(DEADLINE_COLUMN) or task.deadline or ""
        assigned_at = raw.get(ASSIGNED_AT_COLUMN) or getattr(task, "created_at", "") or ""

        self.ensure_sheet()
        self.sheets_client.append_row(
            self.accepted_tasks_sheet_name,
            [report_id, telegram_id, date_value, tasks_done, description, problems, status, feedback, deadline, closed_at, assigned_at],
        )
