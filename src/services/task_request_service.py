from datetime import datetime

from services.google_sheets import GoogleSheetsClient


class TaskRequestService:
    def __init__(self, sheets_client: GoogleSheetsClient, task_requests_sheet_name: str):
        self.sheets_client = sheets_client
        self.task_requests_sheet_name = task_requests_sheet_name

    def create_request(
        self, title: str, description: str, lead_id: int, author_id: int,
    ):
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.sheets_client.append_row(
            self.task_requests_sheet_name,
            [title, description, lead_id, author_id, "offered", created_at],
        )
