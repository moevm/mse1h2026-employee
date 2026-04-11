from __future__ import annotations
from html import escape

from dataclasses import dataclass
from datetime import datetime
import re
import uuid

from constants.sheets_constants import (
    AUTHOR_ID_COLUMN,
    CREATED_AT_COLUMN,
    DEADLINE_COLUMN,
    DESCRIPTION_COLUMN,
    EMPLOYEE_ID_COLUMN,
    STATUS_COLUMN,
    TASK_ID_COLUMN,
    TITLE_COLUMN,
    UPDATED_AT_COLUMN,
)
from services.google_sheets import GoogleSheetsClient

def format_task_for_assignee(task: TaskRecord, author_label: str) -> str:
    title = escape(task.title) if task.title else "—"
    description = escape(task.description) if task.description else "—"
    deadline = escape(task.deadline) if task.deadline else "—"

    return (
        f"<b>Название:</b> {title}\n"
        f"<b>Описание:</b> {description}\n"
        f"<b>Руководитель:</b> {author_label}\n"
        f"<b>Дедлайн:</b> {deadline}"
    )


def format_task_for_lead(task: TaskRecord, assignee_label: str) -> str:
    title = escape(task.title) if task.title else "—"
    description = escape(task.description) if task.description else "—"
    deadline = escape(task.deadline) if task.deadline else "—"
    status = escape(task.status) if task.status else "—"
    updated_at = escape(task.updated_at) if task.updated_at else "—"

    return (
        f"<b>Название:</b> {title}\n"
        f"<b>Описание:</b> {description}\n"
        f"<b>Исполнитель:</b> {assignee_label}\n"
        f"<b>Статус:</b> {status}\n"
        f"<b>Последнее обновление:</b> {updated_at}\n"
        f"<b>Дедлайн:</b> {deadline}"
    )

@dataclass
class TaskRecord:
    row_index: int
    task_id: str
    title: str
    description: str
    employee_id: int | None
    author_id: int | None
    status: str
    created_at: str
    updated_at: str
    deadline: str


class TasksService:
    def __init__(self, sheets_client: GoogleSheetsClient, tasks_sheet_name: str):
        self.sheets_client = sheets_client
        self.tasks_sheet_name = tasks_sheet_name

    @staticmethod
    def _normalize_header(value: str) -> str:
        return re.sub(r"[^a-z0-9]", "", str(value).strip().lower())

    @staticmethod
    def _parse_int(value: str) -> int | None:
        digits = re.sub(r"\D", "", str(value).strip())
        return int(digits) if digits else None

    @staticmethod
    def _now_str() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def find_column(self, headers: list[str], *aliases: str) -> int | None:
        normalized_headers = [self._normalize_header(header) for header in headers]
        normalized_aliases = {self._normalize_header(alias) for alias in aliases}

        for index, header in enumerate(normalized_headers):
            if header in normalized_aliases:
                return index
        return None

    def read_rows(self) -> tuple[list[str], list[list[str]]]:
        values = self.sheets_client.get_all_values(self.tasks_sheet_name)
        if not values:
            return [], []
        return values[0], values[1:]

    def build_task(self, headers: list[str], row: list[str], row_index: int) -> TaskRecord | None:
        task_id_index = self.find_column(headers, TASK_ID_COLUMN)
        title_index = self.find_column(headers, TITLE_COLUMN)
        description_index = self.find_column(headers, DESCRIPTION_COLUMN)
        employee_id_index = self.find_column(headers, EMPLOYEE_ID_COLUMN)
        author_id_index = self.find_column(headers, AUTHOR_ID_COLUMN)
        status_index = self.find_column(headers, STATUS_COLUMN)
        created_at_index = self.find_column(headers, CREATED_AT_COLUMN)
        updated_at_index = self.find_column(headers, UPDATED_AT_COLUMN)
        deadline_index = self.find_column(headers, DEADLINE_COLUMN)

        if task_id_index is None or title_index is None:
            return None

        def value_at(index: int | None) -> str:
            if index is None or index >= len(row):
                return ""
            return str(row[index]).strip()

        task_id = value_at(task_id_index)
        if not task_id:
            return None

        return TaskRecord(
            row_index=row_index,
            task_id=task_id,
            title=value_at(title_index),
            description=value_at(description_index),
            employee_id=self._parse_int(value_at(employee_id_index)),
            author_id=self._parse_int(value_at(author_id_index)),
            status=value_at(status_index),
            created_at=value_at(created_at_index),
            updated_at=value_at(updated_at_index),
            deadline=value_at(deadline_index),
        )

    def get_all_tasks(self) -> list[TaskRecord]:
        headers, rows = self.read_rows()
        if not headers:
            return []

        tasks: list[TaskRecord] = []
        for index, row in enumerate(rows, start=2):
            task = self.build_task(headers, row, index)
            if task is not None:
                tasks.append(task)
        return tasks

    def create_task_created(
        self,
        title: str,
        description: str,
        employee_id: int,
        author_id: int,
        deadline: str,
    ) -> str:
        now = self._now_str()
        task_id = uuid.uuid4().hex

        self.sheets_client.append_row(
            self.tasks_sheet_name,
            [task_id, title, description, employee_id, author_id, "created", now, now, deadline],
        )
        return task_id

    def list_tasks_created_by(self, author_id: int) -> list[TaskRecord]:
        tasks = [task for task in self.get_all_tasks() if task.author_id == author_id]
        return list(reversed(tasks))

    def list_tasks_assigned_to(self, employee_id: int) -> list[TaskRecord]:
        tasks = [task for task in self.get_all_tasks() if task.employee_id == employee_id]
        return list(reversed(tasks))

    def get_task_by_id(self, task_id: str) -> TaskRecord | None:
        for task in self.get_all_tasks():
            if task.task_id == task_id:
                return task
        return None

    def update_task_status(self, task_id: str, new_status: str) -> TaskRecord | None:
        headers, rows = self.read_rows()
        if not headers:
            return None

        task_id_index = self.find_column(headers, TASK_ID_COLUMN, "task_id", "id")
        status_index = self.find_column(headers, STATUS_COLUMN)
        updated_at_index = self.find_column(headers, UPDATED_AT_COLUMN)

        if task_id_index is None or status_index is None or updated_at_index is None:
            return None

        worksheet = self.sheets_client.get_worksheet(self.tasks_sheet_name)
        updated_at_value = self._now_str()

        for offset, row in enumerate(rows, start=2):
            current_task_id = str(row[task_id_index]).strip() if task_id_index < len(row) else ""
            if current_task_id != task_id:
                continue

            worksheet.update_cell(offset, status_index + 1, new_status)
            worksheet.update_cell(offset, updated_at_index + 1, updated_at_value)

            if status_index < len(row):
                row[status_index] = new_status
            if updated_at_index < len(row):
                row[updated_at_index] = updated_at_value

            return self.build_task(headers, row, offset)

        return None
