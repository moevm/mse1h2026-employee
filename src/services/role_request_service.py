from datetime import datetime, timezone

from roles import Role
from services.google_sheets import GoogleSheetsClient
from services.auth_service import AuthService


class RoleRequestService:
    def __init__(
        self, sheets_client: GoogleSheetsClient, role_requests_sheet_name: str
    ):
        self.sheets_client = sheets_client
        self.role_requests_sheet_name = role_requests_sheet_name

    def create_request(self, tg_id: int, role: Role):
        created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.sheets_client.append_row(
            self.role_requests_sheet_name, [tg_id, role.value, created_at]
        )

    def get_all_requests(self) -> list[dict[str, str]]:
        return self.sheets_client.get_all_records(self.role_requests_sheet_name)

    def approve_request(
        self, tg_id: int, role: Role, auth_service: AuthService
    ) -> bool:
        values = self.sheets_client.get_all_values(self.role_requests_sheet_name)

        target_row_index = -1
        for index, row in enumerate(values):
            if len(row) >= 2:
                row_tg_id = str(row[0]).strip()
                row_role = str(row[1]).strip()
                if row_tg_id == str(tg_id).strip() and row_role == role.value:
                    target_row_index = index + 1
                    break

        if target_row_index != -1:
            self.sheets_client.delete_row(
                self.role_requests_sheet_name, target_row_index
            )
            auth_service.grant_role(tg_id, role)
            return True

        return False

    def deny_request(self, tg_id: int, role: Role) -> bool:
        values = self.sheets_client.get_all_values(self.role_requests_sheet_name)

        target_row_index = -1
        for index, row in enumerate(values):
            if len(row) >= 2:
                row_tg_id = str(row[0]).strip()
                row_role = str(row[1]).strip()
                if row_tg_id == str(tg_id).strip() and row_role == role.value:
                    target_row_index = index + 1
                    break

        if target_row_index != -1:
            self.sheets_client.delete_row(
                self.role_requests_sheet_name, target_row_index
            )
            return True

        return False
