from __future__ import annotations

from dataclasses import dataclass

from constants.sheets_constants import ROLE_COLUMN, TG_ID_COLUMN
from roles import Role
from services.google_sheets import GoogleSheetsClient


@dataclass
class AuthUser:
    tg_id: int
    roles: list[Role]


class AuthService:
    def __init__(self, sheets_client: GoogleSheetsClient, roles_sheet_name: str):
        self.sheets_client = sheets_client
        self.roles_sheet_name = roles_sheet_name
        self._active_roles: dict[int, Role] = {}

    def get_user_roles(self, tg_id: int):
        records = self.sheets_client.get_all_records(self.roles_sheet_name)

        roles: list[Role] = []
        normalized_tg_id = str(tg_id).strip()

        for row in records:
            row_tg_id = str(row.get(TG_ID_COLUMN, "")).strip()
            row_role = str(row.get(ROLE_COLUMN, "")).strip()

            if row_tg_id != normalized_tg_id:
                continue

            role = Role.from_str(row_role)

            if role:
                roles.append(role)

        unique_roles = list(dict.fromkeys(roles))
        return unique_roles

    def get_user_ids(self):
        records = self.sheets_client.get_all_records(self.roles_sheet_name)

        tg_ids: list[int] = []

        for row in records:
            row_tg_id = str(row.get(TG_ID_COLUMN, "")).strip()

            if not row_tg_id:
                continue

            tg_ids.append(int(row_tg_id))

        unique_ids = list(dict.fromkeys(tg_ids))
        return unique_ids

    def get_user(self, tg_id: int):
        roles = self.get_user_roles(tg_id)

        if not roles:
            return None

        return AuthUser(
            tg_id=tg_id,
            roles=roles,
        )

    def is_authorized(self, tg_id: int):
        return self.get_user(tg_id) is not None

    def can_login_as_role(self, tg_id: int, role: Role):
        user_roles = self.get_user_roles(tg_id)
        return role in user_roles

    def set_active_role(self, tg_id: int, role: Role):
        self._active_roles[tg_id] = role

    def get_active_role(self, tg_id: int) -> Role | None:
        return self._active_roles.get(tg_id)

    def logout(self, tg_id: int):
        self._active_roles.pop(tg_id, None)
