from datetime import datetime
import uuid

from services.google_sheets import GoogleSheetsClient


class TasksService:
    def __init__(self, sheets_client: GoogleSheetsClient, tasks_sheet_name: str):
        self.sheets_client = sheets_client
        self.tasks_sheet_name = tasks_sheet_name

    def create_task_created(
        self,
        title: str,
        description: str,
        employee_id: int,
        author_id: int,
        deadline: str,  # YYYY-MM-DD
    ) -> str:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task_id = uuid.uuid4().hex

        # TaskId Title Description EmployeeID AuthorID Status CreatedAt UpdatedAt Deadline
        self.sheets_client.append_row(
            self.tasks_sheet_name,
            [task_id, title, description, employee_id, author_id, "created", now, now, deadline],
        )
        return task_id