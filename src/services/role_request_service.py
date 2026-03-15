from roles import Role
from services.google_sheets import GoogleSheetsClient


class RoleRequestService:
    def __init__(self, sheets_client: GoogleSheetsClient, role_requests_sheet_name: str):
        self.sheets_client = sheets_client
        self.role_requests_sheet_name = role_requests_sheet_name

    def create_request(self, tg_id: int, role: Role):
        # В лист "Запросы ролей": Telegram ID | Role
        self.sheets_client.append_row(self.role_requests_sheet_name, [tg_id, role.value])