from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
import uuid

from constants.sheets_constants import EMPLOYEE_ID_COLUMN, TASK_ID_COLUMN, CREATED_AT_COLUMN
from services.google_sheets import GoogleSheetsClient


@dataclass
class ReportRecord:
    row_index: int
    report_id: str
    task_id: str
    employee_id: int | None
    text: str
    created_at: str
    raw_fields: dict[str, str]


class ReportsService:
    def __init__(self, sheets_client: GoogleSheetsClient, reports_sheet_name: str):
        self.sheets_client = sheets_client
        self.reports_sheet_name = reports_sheet_name

    @staticmethod
    def _normalize_header(value: str) -> str:
        return re.sub(r"[^a-z0-9а-яё]", "", str(value).strip().lower())

    @staticmethod
    def _parse_int(value: str) -> int | None:
        digits = re.sub(r"\D", "", str(value).strip())
        return int(digits) if digits else None

    def find_column(self, headers: list[str], *aliases: str) -> int | None:
        normalized_headers = [self._normalize_header(header) for header in headers]
        normalized_aliases = {self._normalize_header(alias) for alias in aliases}

        for index, header in enumerate(normalized_headers):
            if header in normalized_aliases:
                return index
        return None

    def read_rows(self) -> tuple[list[str], list[list[str]]]:
        values = self.sheets_client.get_all_values(self.reports_sheet_name)
        if not values:
            return [], []
        return values[0], values[1:]

    def build_report(self, headers: list[str], row: list[str], row_index: int) -> ReportRecord | None:
        report_id_index = self.find_column(headers, "ReportID", "ReportId", "report_id")
        task_id_index = self.find_column(headers, TASK_ID_COLUMN, "task_id")
        employee_id_index = self.find_column(headers, EMPLOYEE_ID_COLUMN, "TelegramID", "employee_id")
        text_index = self.find_column(headers, "Text", "ReportText", "text")
        created_at_index = self.find_column(headers, CREATED_AT_COLUMN, "Date", "created_at")

        if report_id_index is None or task_id_index is None:
            return None

        def value_at(index: int | None) -> str:
            if index is None or index >= len(row):
                return ""
            return str(row[index]).strip()

        report_id = value_at(report_id_index)
        task_id = value_at(task_id_index)
        if not report_id or not task_id:
            return None

        text = value_at(text_index)

        raw_fields: dict[str, str] = {}
        for index, header in enumerate(headers):
            raw_fields[str(header).strip()] = str(row[index]).strip() if index < len(row) else ""

        return ReportRecord(
            row_index=row_index,
            report_id=report_id,
            task_id=task_id,
            employee_id=self._parse_int(value_at(employee_id_index)),
            text=text,
            created_at=value_at(created_at_index),
            raw_fields=raw_fields,
        )

    def get_all_reports(self) -> list[ReportRecord]:
        headers, rows = self.read_rows()
        if not headers:
            return []

        reports: list[ReportRecord] = []
        for index, row in enumerate(rows, start=2):
            report = self.build_report(headers, row, index)
            if report is not None:
                reports.append(report)
        return reports

    def get_report_by_id(self, report_id: str) -> ReportRecord | None:
        normalized_report_id = str(report_id).strip()
        for report in self.get_all_reports():
            if report.report_id == normalized_report_id:
                return report
        return None

    def get_report_by_task_id(self, task_id: str) -> ReportRecord | None:
        normalized_task_id = str(task_id).strip()
        for report in self.get_all_reports():
            if report.task_id == normalized_task_id:
                return report
        return None

    def create_report(self, task_id: str, employee_id: int, text: str) -> str:
        existing_report = self.get_report_by_task_id(task_id)
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if existing_report is not None:
            self.update_report_by_task_id(task_id, employee_id, text, created_at)
            return existing_report.report_id

        report_id = uuid.uuid4().hex
        self.sheets_client.append_row(
            self.reports_sheet_name,
            [report_id, task_id, employee_id, text, created_at, ""],
        )
        return report_id

    def update_report_by_task_id(self, task_id: str, employee_id: int, text: str, created_at: str | None = None) -> bool:
        headers, rows = self.read_rows()
        if not headers:
            return False

        report_id_index = self.find_column(headers, "ReportID", "ReportId", "report_id")
        task_id_index = self.find_column(headers, TASK_ID_COLUMN, "task_id")
        employee_id_index = self.find_column(headers, EMPLOYEE_ID_COLUMN, "TelegramID", "employee_id")
        text_index = self.find_column(headers, "Text", "ReportText", "text")
        created_at_index = self.find_column(headers, CREATED_AT_COLUMN, "Date", "created_at")
        feedback_index = self.find_column(headers, "ManagerFeedback", "manager_feedback", "Комментарий руководителя")

        if task_id_index is None or text_index is None:
            return False

        normalized_task_id = str(task_id).strip()
        created_at_value = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for row_index, row in enumerate(rows, start=2):
            current_task_id = str(row[task_id_index]).strip() if task_id_index < len(row) else ""
            if current_task_id == normalized_task_id:
                if employee_id_index is not None:
                    self.sheets_client.update_cell(
                        self.reports_sheet_name,
                        row_index,
                        employee_id_index + 1,
                        str(employee_id),
                    )
                if text_index is not None:
                    self.sheets_client.update_cell(
                        self.reports_sheet_name,
                        row_index,
                        text_index + 1,
                        text,
                    )
                if created_at_index is not None:
                    self.sheets_client.update_cell(
                        self.reports_sheet_name,
                        row_index,
                        created_at_index + 1,
                        created_at_value,
                    )
                if feedback_index is not None:
                    self.sheets_client.update_cell(
                        self.reports_sheet_name,
                        row_index,
                        feedback_index + 1,
                        "",
                    )
                return True

        return False

    def update_manager_feedback(self, task_id: str, feedback: str) -> bool:
        headers, rows = self.read_rows()
        if not headers:
            return False

        feedback_index = self.find_column(
            headers,
            "ManagerFeedback",
        )
        task_id_index = self.find_column(headers, TASK_ID_COLUMN, "task_id")

        if feedback_index is None or task_id_index is None:
            return False

        normalized_task_id = str(task_id).strip()

        for row_index, row in enumerate(rows, start=2):
            current_task_id = str(row[task_id_index]).strip() if task_id_index < len(row) else ""
            if current_task_id == normalized_task_id:
                self.sheets_client.update_cell(
                    self.reports_sheet_name,
                    row_index,
                    feedback_index + 1,
                    feedback,
                )
                return True

        return False

    def get_manager_feedback_by_task_id(self, task_id: str) -> str:
        report = self.get_report_by_task_id(task_id)
        if report is None:
            return ""

        for key, value in report.raw_fields.items():
            if self._normalize_header(key) in {
                self._normalize_header("ManagerFeedback"),
            }:
                return str(value).strip()

        return ""

    def delete_report_by_task_id(self, task_id: str) -> bool:
        report = self.get_report_by_task_id(task_id)
        if report is None:
            return False

        self.sheets_client.delete_row(self.reports_sheet_name, report.row_index)
        return True