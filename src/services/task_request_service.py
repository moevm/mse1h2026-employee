from datetime import datetime

from services.google_sheets import GoogleSheetsClient


class TaskRequestService:
    def __init__(self, sheets_client: GoogleSheetsClient, task_requests_sheet_name: str):
        self.sheets_client = sheets_client
        self.task_requests_sheet_name = task_requests_sheet_name

    def create_request(
        self,
        title: str,
        description: str,
        lead_id: int,
        author_id: int,
        created_at: str | None = None,
    ):
        created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.sheets_client.append_row(
            self.task_requests_sheet_name,
            [title, description, lead_id, author_id, "offered", created_at],
        )

    def create_requests(
        self,
        title: str,
        description: str,
        lead_ids: list[int],
        author_id: int,
    ) -> int:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        unique_lead_ids = list(dict.fromkeys(lead_ids))

        for lead_id in unique_lead_ids:
            self.create_request(
                title=title,
                description=description,
                lead_id=lead_id,
                author_id=author_id,
                created_at=created_at,
            )

        return len(unique_lead_ids)
