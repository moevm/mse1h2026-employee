from __future__ import annotations

from datetime import date

from services.accepted_tasks_service import AcceptedTasksService
from services.daily_reports_service import DailyReportsService
from services.tasks_service import TasksService
from services.visits_service import VisitsService


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


def test_weekly_report_services_count_tasks_hours_overdue_and_missing_reports():
    sheets = FakeSheetsClient(
        {
            "Принятые задачи": [
                ["ReportID", "TelegramID", "Date", "TasksDone", "Description", "Problems", "Status", "ManagerFeedback", "Deadline", "ClosedAt", "AssignedAt"],
                ["r1", "100", "2026-05-18 18:10:00", "Задача 1", "Описание 1", "", "accepted", "", "2026-05-20", "2026-05-18 18:10:00", "2026-05-18 09:00:00"],
                ["r2", "100", "2026-05-20", "Задача 2", "Описание 2", "", "accepted", "", "2026-05-19", "2026-05-20 19:00:00", "2026-05-18 09:30:00"],
                ["r3", "100", "2026-05-18", "Просрочка со старым дедлайном", "", "", "accepted", "", "2026-05-17", "2026-05-18", "2026-05-15"],
                ["r6", "100", "2026-05-22", "Закрыта позже по дедлайну недели", "", "", "accepted", "", "2026-05-20", "2026-05-22", "2026-05-18"],
                ["r4", "101", "2026-05-18", "Чужая", "", "", "accepted", "", "2026-05-18", "2026-05-18", "2026-05-18"],
                ["r5", "100", "2026-05-19", "Не принята", "", "", "rejected", "", "2026-05-18", "2026-05-19", "2026-05-18"],
            ],
            "Задачи": [
                ["TaskId", "Title", "Description", "EmployeeID", "AuthorID", "Status", "CreatedAt", "UpdatedAt", "Deadline"],
                ["t1", "Назначенная", "Описание назначенной", "100", "200", "created", "2026-05-18 10:00:00", "2026-05-18 10:00:00", "2026-05-30"],
                ["t2", "Открытая просрочка", "Описание просрочки", "100", "200", "in process", "2026-05-01", "2026-05-18", "2026-05-18"],
                ["t5", "Старый дедлайн", "Не попадает в выбранную неделю", "100", "200", "in process", "2026-05-01", "2026-05-18", "2026-05-17"],
                ["t3", "Будущая", "Описание будущей", "100", "200", "in process", "2026-05-19", "2026-05-19", "2026-05-25"],
                ["t4", "Чужая", "", "101", "200", "created", "2026-05-18", "2026-05-18", "2026-05-18"],
            ],
            "Посещения": [
                ["Telegram ID", "StartedAt", "EndedAt"],
                ["100", "2026-05-18 09:03:00", "2026-05-18 17:03:00"],
                ["100", "2026-05-19 09:12:00", "2026-05-19 17:42:00"],
                ["101", "2026-05-18 10:00:00", "2026-05-18 11:00:00"],
                ["100", "2026-05-17 09:00:00", "2026-05-17 10:00:00"],
            ],
            "Ежедневные отчеты": [
                DailyReportsService.HEADERS,
                ["d1", "100", "2026-05-18", "Работа", "", "1", "Задача 1", "0", "", "2026-05-18 18:00:00"],
                ["d2", "101", "2026-05-19", "Чужой", "", "1", "X", "0", "", "2026-05-19 18:00:00"],
            ],
        }
    )

    accepted = AcceptedTasksService(sheets, "Принятые задачи")
    tasks = TasksService(sheets, "Задачи")
    visits = VisitsService(sheets, "Посещения")
    daily_reports = DailyReportsService(sheets, "Ежедневные отчеты")

    week_start = date(2026, 5, 18)
    week_end = date(2026, 5, 20)
    report_dates = [date(2026, 5, 18), date(2026, 5, 19), date(2026, 5, 20)]

    closed = accepted.list_closed_tasks_for_employee_between(100, week_start, week_end)
    assert [task.task_title for task in closed] == ["Задача 1", "Задача 2", "Просрочка со старым дедлайном"]
    assert closed[0].assigned_at == "2026-05-18 09:00:00"
    assert accepted.count_closed_tasks_for_employee_between(100, week_start, week_end) == 3
    overdue_closed = accepted.list_closed_overdue_tasks_for_employee_between(100, week_start, week_end)
    assert [task.task_title for task in overdue_closed] == ["Задача 2", "Закрыта позже по дедлайну недели"]

    assigned = tasks.list_tasks_assigned_to_between(100, week_start, week_end)
    assert [task.title for task in assigned] == ["Будущая", "Назначенная"]
    open_overdue = tasks.list_open_overdue_tasks_for_employee_between(100, week_start, week_end)
    assert [task.title for task in open_overdue] == ["Открытая просрочка"]

    assert visits.sum_worked_hours_for_employee_between(100, week_start, week_end) == 16.5
    assert daily_reports.count_missing_reports_for_employee_between(100, report_dates) == 2
