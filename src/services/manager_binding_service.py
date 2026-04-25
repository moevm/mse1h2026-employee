from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from constants.sheets_constants import (
    BIND_CREATED_AT_COLUMN,
    BIND_EMPLOYEE_ID_COLUMN,
    BIND_EMPLOYEE_ROLE_COLUMN,
    BIND_LEAD_ID_COLUMN,
    BIND_REQUEST_ID_COLUMN,
)
from roles import Role
from services.google_sheets import GoogleSheetsClient


@dataclass
class ManagerBindRequest:
    request_id: str
    employee_id: int
    employee_role: Role
    lead_id: int
    created_at: str


class ManagerBindingService:
    def __init__(self, sheets_client: GoogleSheetsClient, sheet_name: str):
        self.sheets_client = sheets_client
        self.sheet_name = sheet_name

    @staticmethod
    def _parse_int(value: object) -> int | None:
        raw = str(value).strip()
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    def _record_to_request(self, row: dict[str, object]) -> ManagerBindRequest | None:
        request_id = str(row.get(BIND_REQUEST_ID_COLUMN, "")).strip()
        employee_id = self._parse_int(row.get(BIND_EMPLOYEE_ID_COLUMN, ""))
        lead_id = self._parse_int(row.get(BIND_LEAD_ID_COLUMN, ""))
        employee_role = Role.from_str(str(row.get(BIND_EMPLOYEE_ROLE_COLUMN, "")).strip())
        created_at = str(row.get(BIND_CREATED_AT_COLUMN, "")).strip()

        if not request_id or employee_id is None or lead_id is None or employee_role is None:
            return None

        return ManagerBindRequest(
            request_id=request_id,
            employee_id=employee_id,
            employee_role=employee_role,
            lead_id=lead_id,
            created_at=created_at,
        )

    def create_request(self, employee_id: int, employee_role: Role, lead_id: int) -> ManagerBindRequest | None:
        if employee_id == lead_id:
            return None

        existing = self.get_request(employee_id, employee_role, lead_id)
        if existing:
            return None

        request = ManagerBindRequest(
            request_id=uuid4().hex,
            employee_id=employee_id,
            employee_role=employee_role,
            lead_id=lead_id,
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.sheets_client.append_row(
            self.sheet_name,
            [
                request.request_id,
                request.employee_id,
                request.employee_role.value,
                request.lead_id,
                request.created_at,
            ],
        )
        return request

    def get_request(self, employee_id: int, employee_role: Role, lead_id: int) -> ManagerBindRequest | None:
        for request in self.list_requests_for_lead(lead_id):
            if request.employee_id == employee_id and request.employee_role == employee_role:
                return request
        return None

    def list_requests_for_lead(self, lead_id: int) -> list[ManagerBindRequest]:
        records = self.sheets_client.get_all_records(self.sheet_name)
        requests: list[ManagerBindRequest] = []
        for row in records:
            request = self._record_to_request(row)
            if request and request.lead_id == lead_id:
                requests.append(request)
        return requests

    def get_request_by_id(self, request_id: str, lead_id: int | None = None) -> ManagerBindRequest | None:
        records = self.sheets_client.get_all_records(self.sheet_name)
        for row in records:
            request = self._record_to_request(row)
            if not request:
                continue
            if request.request_id != request_id:
                continue
            if lead_id is not None and request.lead_id != lead_id:
                continue
            return request
        return None

    def delete_request(self, request_id: str) -> bool:
        values = self.sheets_client.get_all_values(self.sheet_name)
        if not values:
            return False

        headers = values[0]
        request_id_index = next(
            (index for index, header in enumerate(headers) if str(header).strip() == BIND_REQUEST_ID_COLUMN),
            None,
        )
        if request_id_index is None:
            return False

        for row_index, row in enumerate(values[1:], start=2):
            row_request_id = str(row[request_id_index]).strip() if request_id_index < len(row) else ""
            if row_request_id == request_id:
                self.sheets_client.delete_row(self.sheet_name, row_index)
                return True

        return False