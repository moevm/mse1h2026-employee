from __future__ import annotations

from services.accepted_tasks_service import AcceptedTasksService
from services.daily_reports_service import DailyReportsService


class FakeSheetsClient:
    def __init__(self, initial: dict[str, list[list[str]]] | None = None):
        self.values = {name: [list(row) for row in rows] for name, rows in (initial or {}).items()}
        self.append_calls: list[tuple[str, list[str]]] = []
        self.update_calls: list[tuple[str, int, int, str]] = []
        self.ensured_headers: list[tuple[str, list[str]]] = []

    def ensure_headers(self, sheet_name: str, headers: list[str]):
        self.ensured_headers.append((sheet_name, list(headers)))
        rows = self.values.setdefault(sheet_name, [])
        if not rows:
            rows.append(list(headers))
            return None

        existing = list(rows[0])
        for header in headers:
            if header not in existing:
                existing.append(header)
        rows[0] = existing
        return None

    def get_all_values(self, sheet_name: str):
        return [list(row) for row in self.values.get(sheet_name, [])]

    def append_row(self, sheet_name: str, values: list[str]):
        self.append_calls.append((sheet_name, list(values)))
        self.values.setdefault(sheet_name, []).append([str(value) for value in values])

    def update_cell(self, sheet_name: str, row: int, col: int, value: str):
        self.update_calls.append((sheet_name, row, col, str(value)))
        rows = self.values.setdefault(sheet_name, [])
        while len(rows) < row:
            rows.append([])
        while len(rows[row - 1]) < col:
            rows[row - 1].append("")
        rows[row - 1][col - 1] = str(value)


def test_daily_reports_service_creates_updates_and_filters_reports_by_date_and_team():
    sheets = FakeSheetsClient()
    service = DailyReportsService(sheets, "Ежедневные отчеты")

    report_id, was_updated = service.create_or_update_report(
        employee_id=100,
        report_date="2026-05-17 12:00:00",
        work_done="Сделал задачи",
        problems="",
        completed_tasks_titles=["Готовая", "Принятая"],
        in_process_tasks_titles=["В процессе"],
    )

    assert was_updated is False
    assert report_id
    assert sheets.values["Ежедневные отчеты"][0] == DailyReportsService.HEADERS
    appended = sheets.append_calls[0][1]
    assert appended[0] == report_id
    assert appended[1] == "100"
    assert appended[2] == "2026-05-17"
    assert appended[5] == 2
    assert appended[6] == "Готовая\nПринятая"
    assert appended[7] == 1
    assert appended[8] == "В процессе"

    same_report_id, was_updated = service.create_or_update_report(
        employee_id=100,
        report_date="2026-05-17",
        work_done="Обновил отчет",
        problems="Блокер",
        completed_tasks_titles=["Готовая"],
        in_process_tasks_titles=[],
    )

    assert same_report_id == report_id
    assert was_updated is True
    assert ("Ежедневные отчеты", 2, 4, "Обновил отчет") in sheets.update_calls
    assert ("Ежедневные отчеты", 2, 6, "1") in sheets.update_calls
    assert ("Ежедневные отчеты", 2, 8, "0") in sheets.update_calls

    sheets.append_row(
        "Ежедневные отчеты",
        ["foreign", "101", "2026-05-17", "Чужой", "", "1", "X", "0", "", "2026-05-17 18:00:00"],
    )
    sheets.append_row(
        "Ежедневные отчеты",
        ["old", "100", "2026-05-16", "Старый", "", "1", "Y", "0", "", "2026-05-16 18:00:00"],
    )

    reports = service.list_reports_for_date("2026-05-17", [100])
    assert [report.report_id for report in reports] == [report_id]
    assert reports[0].work_done == "Обновил отчет"
    assert reports[0].completed_tasks_count == 1
    assert reports[0].in_process_tasks_count == 0


def test_accepted_tasks_service_returns_unique_titles_for_employee_and_date():
    sheets = FakeSheetsClient(
        {
            "Принятые задачи": [
                ["ReportID", "TelegramID", "Date", "TasksDone", "Description", "Problems", "Status", "ManagerFeedback"],
                ["r1", "100", "2026-05-17 10:00:00", "Принятая", "", "", "accepted", ""],
                ["r2", "100", "2026-05-17", "Принятая", "", "", "accepted", ""],
                ["r3", "100", "2026-05-16", "Вчерашняя", "", "", "accepted", ""],
                ["r4", "101", "2026-05-17", "Чужая", "", "", "accepted", ""],
                ["r5", "100", "2026-05-17", "Еще одна", "", "", "accepted", ""],
            ]
        }
    )
    service = AcceptedTasksService(sheets, "Принятые задачи")

    assert service.list_task_titles_for_employee_on_date(100, "2026-05-17") == [
        "Принятая",
        "Еще одна",
    ]
