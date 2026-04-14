from __future__ import annotations

from datetime import datetime

from services.google_sheets import GoogleSheetsClient
from services.reports_service import ReportRecord
from services.tasks_service import TaskRecord


class AcceptedTasksService:
    def __init__(self, sheets_client: GoogleSheetsClient, accepted_tasks_sheet_name: str):
        self.sheets_client = sheets_client
        self.accepted_tasks_sheet_name = accepted_tasks_sheet_name

    @staticmethod
    def _now_str() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

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
