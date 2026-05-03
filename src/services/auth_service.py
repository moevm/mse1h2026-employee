from __future__ import annotations

from dataclasses import dataclass
import re

from constants.sheets_constants import (
    MANAGER_IDS_COLUMN,
    NOTIFICATION_EVENING_TIME_COLUMN,
    NOTIFICATION_MORNING_TIME_COLUMN,
    NOTIFICATION_TIMEZONE_COLUMN,
    ROLE_COLUMN,
    TG_ID_COLUMN,
)
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
    
    def get_manager_ids_for_user(self, tg_id: int, role: Role | None = None):
        records = self.sheets_client.get_all_records(self.roles_sheet_name)

        manager_ids: list[int] = []
        normalized_tg_id = str(tg_id).strip()

        for row in records:
            row_tg_id = str(row.get(TG_ID_COLUMN, "")).strip()
            row_role = Role.from_str(str(row.get(ROLE_COLUMN, "")).strip())

            if row_tg_id != normalized_tg_id:
                continue

            if role and row_role != role:
                continue

            raw_manager_ids = str(row.get(MANAGER_IDS_COLUMN, "")).strip()
            if not raw_manager_ids:
                continue

            for value in re.split(r"[,;\n]+", raw_manager_ids):
                digits = re.sub(r"\D", "", value)
                if digits:
                    manager_ids.append(int(digits))

        return list(dict.fromkeys(manager_ids))
    
    def get_team_members_for_manager(
        self,
        manager_id: int,
        allowed_roles: tuple[Role, ...] = (Role.EMPLOYEE, Role.INTERN),
    ) -> list[int]:
        records = self.sheets_client.get_all_records(self.roles_sheet_name)

        member_ids: list[int] = []

        for row in records:
            row_role = Role.from_str(str(row.get(ROLE_COLUMN, "")).strip())
            if row_role not in allowed_roles:
                continue

            row_tg_id = str(row.get(TG_ID_COLUMN, "")).strip()
            if not row_tg_id:
                continue

            raw_manager_ids = str(row.get(MANAGER_IDS_COLUMN, "")).strip()
            if not raw_manager_ids:
                continue

            manager_ids: list[int] = []
            for value in re.split(r"[,;\n]+", raw_manager_ids):
                digits = re.sub(r"\D", "", value)
                if digits:
                    manager_ids.append(int(digits))

            if manager_id in manager_ids:
                member_ids.append(int(row_tg_id))

        return list(dict.fromkeys(member_ids))

    def get_employees_for_manager(self, manager_id: int) -> list[int]:
        return self.get_team_members_for_manager(manager_id, (Role.EMPLOYEE,))

    def _ensure_roles_column(self, column_name: str) -> int:
        values = self.sheets_client.get_all_values(self.roles_sheet_name)
        headers = values[0] if values else []

        for index, header in enumerate(headers, start=1):
            if str(header).strip() == column_name:
                return index

        worksheet = self.sheets_client.get_worksheet(self.roles_sheet_name)
        col_index = len(headers) + 1
        worksheet.update_cell(1, col_index, column_name)
        return col_index

    def _find_roles_column(self, headers: list[str], column_name: str) -> int | None:
        return next(
            (index + 1 for index, header in enumerate(headers) if str(header).strip() == column_name),
            None,
        )

    def get_notification_settings(self, tg_id: int, default_morning_time: str, default_evening_time: str, default_timezone: str) -> dict[str, str]:
        values = self.sheets_client.get_all_values(self.roles_sheet_name)
        if not values:
            return {
                "morning_time": default_morning_time,
                "evening_time": default_evening_time,
                "timezone": default_timezone,
            }

        headers = values[0]
        tg_col = self._find_roles_column(headers, TG_ID_COLUMN)
        morning_col = self._find_roles_column(headers, NOTIFICATION_MORNING_TIME_COLUMN)
        evening_col = self._find_roles_column(headers, NOTIFICATION_EVENING_TIME_COLUMN)
        timezone_col = self._find_roles_column(headers, NOTIFICATION_TIMEZONE_COLUMN)

        if tg_col is None:
            return {
                "morning_time": default_morning_time,
                "evening_time": default_evening_time,
                "timezone": default_timezone,
            }

        normalized_tg_id = str(tg_id).strip()
        for row in values[1:]:
            row_tg_id = str(row[tg_col - 1]).strip() if tg_col - 1 < len(row) else ""
            if row_tg_id != normalized_tg_id:
                continue

            morning_time = str(row[morning_col - 1]).strip() if morning_col and morning_col - 1 < len(row) else ""
            evening_time = str(row[evening_col - 1]).strip() if evening_col and evening_col - 1 < len(row) else ""
            timezone = str(row[timezone_col - 1]).strip() if timezone_col and timezone_col - 1 < len(row) else ""

            return {
                "morning_time": morning_time or default_morning_time,
                "evening_time": evening_time or default_evening_time,
                "timezone": timezone or default_timezone,
            }

        return {
            "morning_time": default_morning_time,
            "evening_time": default_evening_time,
            "timezone": default_timezone,
        }

    def set_notification_settings(self, tg_id: int, morning_time: str, evening_time: str, timezone: str) -> bool:
        values = self.sheets_client.get_all_values(self.roles_sheet_name)
        if not values:
            return False

        headers = values[0]
        tg_col = self._find_roles_column(headers, TG_ID_COLUMN)
        if tg_col is None:
            return False

        morning_col = self._ensure_roles_column(NOTIFICATION_MORNING_TIME_COLUMN)
        evening_col = self._ensure_roles_column(NOTIFICATION_EVENING_TIME_COLUMN)
        timezone_col = self._ensure_roles_column(NOTIFICATION_TIMEZONE_COLUMN)

        normalized_tg_id = str(tg_id).strip()
        updated = False

        for row_index, row in enumerate(values[1:], start=2):
            row_tg_id = str(row[tg_col - 1]).strip() if tg_col - 1 < len(row) else ""
            if row_tg_id != normalized_tg_id:
                continue

            self.sheets_client.update_cell(self.roles_sheet_name, row_index, morning_col, morning_time)
            self.sheets_client.update_cell(self.roles_sheet_name, row_index, evening_col, evening_time)
            self.sheets_client.update_cell(self.roles_sheet_name, row_index, timezone_col, timezone)
            updated = True

        return updated

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

    def grant_role(self, tg_id: int, role: Role):
        self.sheets_client.append_row(self.roles_sheet_name, [tg_id, role.value])