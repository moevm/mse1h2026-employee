from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re
import uuid

from constants.sheets_constants import (
    AUTHOR_ID_COLUMN,
    CREATED_AT_COLUMN,
    DESCRIPTION_COLUMN,
    LEAD_ID_COLUMN,
    OFFER_ID_COLUMN,
    STATUS_COLUMN,
    TITLE_COLUMN,
)
from services.google_sheets import GoogleSheetsClient


@dataclass
class TaskRequestRecord:
    row_index: int
    offer_id: str
    title: str
    description: str
    lead_id: int | None
    author_id: int | None
    status: str
    created_at: str

    @property
    def callback_token(self) -> str:
        return self.offer_id


class TaskRequestService:
    def __init__(self, sheets_client: GoogleSheetsClient, task_requests_sheet_name: str):
        self.sheets_client = sheets_client
        self.task_requests_sheet_name = task_requests_sheet_name

    @staticmethod
    def _normalize_header(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", str(value).strip().lower())

    @staticmethod
    def _parse_int(value: str) -> int | None:
        digits = re.sub(r"\D", "", str(value).strip())
        return int(digits) if digits else None

    def find_column(self, headers: list[str], *aliases: str) -> int | None:
        normalized_headers = [self._normalize_header(header) for header in headers]
        normalized_aliases = {self._normalize_header(alias) for alias in aliases}

        for index, header in enumerate(normalized_headers):
            if header in normalized_aliases:
                return index

        return None

    def read_rows(self) -> tuple[list[str], list[list[str]]]:
        values = self.sheets_client.get_all_values(self.task_requests_sheet_name)
        if not values:
            return [], []

        return values[0], values[1:]

    def build_request(
        self,
        headers: list[str],
        row: list[str],
        row_index: int,
    ) -> TaskRequestRecord | None:
        offer_id_index = self.find_column(headers, OFFER_ID_COLUMN)
        title_index = self.find_column(headers, TITLE_COLUMN)
        description_index = self.find_column(headers, DESCRIPTION_COLUMN)
        lead_id_index = self.find_column(headers, LEAD_ID_COLUMN)
        author_id_index = self.find_column(headers, AUTHOR_ID_COLUMN)
        status_index = self.find_column(headers, STATUS_COLUMN)
        created_at_index = self.find_column(headers, CREATED_AT_COLUMN)

        if (
            offer_id_index is None
            or title_index is None
            or lead_id_index is None
            or author_id_index is None
        ):
            return None

        def value_at(index: int | None) -> str:
            if index is None or index >= len(row):
                return ""
            return str(row[index]).strip()

        offer_id = value_at(offer_id_index)
        title = value_at(title_index)
        lead_id = self._parse_int(value_at(lead_id_index))
        author_id = self._parse_int(value_at(author_id_index))

        if not offer_id or not title or lead_id is None or author_id is None:
            return None

        return TaskRequestRecord(
            row_index=row_index,
            offer_id=offer_id,
            title=title,
            description=value_at(description_index),
            lead_id=lead_id,
            author_id=author_id,
            status=value_at(status_index),
            created_at=value_at(created_at_index),
        )

    def get_all_requests(self) -> list[TaskRequestRecord]:
        headers, rows = self.read_rows()
        if not headers:
            return []

        requests: list[TaskRequestRecord] = []

        for index, row in enumerate(rows, start=2):
            request = self.build_request(headers, row, index)
            if request is not None:
                requests.append(request)

        return requests

    def list_requests_for_lead(self, lead_id: int) -> list[TaskRequestRecord]:
        requests = [
            request
            for request in self.get_all_requests()
            if request.lead_id == lead_id
            and request.status.strip().lower() == "offered"
        ]

        return list(reversed(requests))

    def get_request_for_lead_by_token(
        self,
        token: str | None,
        lead_id: int,
    ) -> TaskRequestRecord | None:
        if not token:
            return None

        token = str(token).strip()

        for request in self.get_all_requests():
            if request.offer_id == token and request.lead_id == lead_id:
                return request

        return None

    def delete_request(self, request: TaskRequestRecord) -> int:
        return self.sheets_client.delete_rows_batch(
            self.task_requests_sheet_name,
            [request.row_index],
        )

    def delete_related_requests(self, request: TaskRequestRecord) -> int:
        related_row_indices = [
            candidate.row_index
            for candidate in self.get_all_requests()
            if candidate.offer_id == request.offer_id
        ]

        return self.sheets_client.delete_rows_batch(
            self.task_requests_sheet_name,
            related_row_indices,
        )

    def _build_request_row(
        self,
        headers: list[str],
        offer_id: str,
        title: str,
        description: str,
        lead_id: int,
        author_id: int,
        status: str,
        created_at: str,
    ) -> list[str]:
        values_by_header = {
            self._normalize_header(OFFER_ID_COLUMN): offer_id,
            self._normalize_header(TITLE_COLUMN): title,
            self._normalize_header(DESCRIPTION_COLUMN): description,
            self._normalize_header(LEAD_ID_COLUMN): lead_id,
            self._normalize_header(AUTHOR_ID_COLUMN): author_id,
            self._normalize_header(STATUS_COLUMN): status,
            self._normalize_header(CREATED_AT_COLUMN): created_at,
        }

        return [
            values_by_header.get(self._normalize_header(header), "")
            for header in headers
        ]

    def create_requests(
        self,
        title: str,
        description: str,
        lead_ids: list[int],
        author_id: int,
    ) -> int:
        headers, _ = self.read_rows()

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        offer_id = uuid.uuid4().hex
        unique_lead_ids = list(dict.fromkeys(lead_ids))

        rows = [
            self._build_request_row(
                headers=headers,
                offer_id=offer_id,
                title=title,
                description=description,
                lead_id=lead_id,
                author_id=author_id,
                status="offered",
                created_at=created_at,
            )
            for lead_id in unique_lead_ids
        ]

        self.sheets_client.append_rows(self.task_requests_sheet_name, rows)
        return len(unique_lead_ids)