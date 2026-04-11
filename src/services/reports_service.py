from datetime import datetime
import uuid

from services.google_sheets import GoogleSheetsClient


class ReportsService:
    def __init__(self, sheets_client: GoogleSheetsClient, reports_sheet_name: str):
        self.sheets_client = sheets_client
        self.reports_sheet_name = reports_sheet_name

    def create_report(self, task_id: str, employee_id: int, text: str) -> str:
        report_id = uuid.uuid4().hex
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ReportId | TaskId | EmployeeID | Text | CreatedAt
        self.sheets_client.append_row(
            self.reports_sheet_name,
            [report_id, task_id, employee_id, text, created_at],
        )
        return report_id