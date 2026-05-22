from __future__ import annotations

from dataclasses import replace
from typing import Any

from conftest import FakeBot, FakeMessage, FakeState

from roles import Role
from services.daily_reports_service import DailyReportRecord
from services.manager_binding_service import ManagerBindRequest
from services.reports_service import ReportRecord
from services.accepted_tasks_service import AcceptedTaskRecord
from services.task_request_service import TaskRequestRecord
from services.tasks_service import TaskRecord


class FakeVisitsService:
    def __init__(
        self,
        *,
        start_result: bool = True,
        finish_result: bool = True,
        open_visit: bool = False,
    ):
        self.start_result = start_result
        self.finish_result = finish_result
        self.open_visit = open_visit
        self.started_for: list[int] = []
        self.finished_for: list[int] = []

    def start_workday(self, tg_id: int) -> bool:
        self.started_for.append(tg_id)
        return self.start_result

    def finish_workday(self, tg_id: int) -> bool:
        self.finished_for.append(tg_id)
        return self.finish_result

    def has_open_visit(self, tg_id: int) -> bool:
        return self.open_visit


class FakeAuthService:
    def __init__(
        self,
        *,
        lead_ids: list[int] | None = None,
        manager_ids_by_key: dict[tuple[int, Role], list[int]] | None = None,
        active_roles: dict[int, Role] | None = None,
    ):
        self.lead_ids = lead_ids or []
        self.manager_ids_by_key = manager_ids_by_key or {}
        self.active_roles = active_roles or {}
        self.logged_out: list[int] = []

    def get_user_ids_by_role(self, role: Role) -> list[int]:
        return list(self.lead_ids) if role == Role.LEAD else []

    def get_manager_ids_for_user(
        self, tg_id: int, role: Role | None = None
    ) -> list[int]:
        return list(self.manager_ids_by_key.get((tg_id, role), []))

    def get_active_role(self, tg_id: int) -> Role | None:
        return self.active_roles.get(tg_id)

    def logout(self, tg_id: int) -> None:
        self.logged_out.append(tg_id)
        self.active_roles.pop(tg_id, None)


class FakeManagerBindingService:
    def __init__(self, *, create_result: object | None = object()):
        self.create_result = create_result
        self.create_calls: list[tuple[int, Role, int]] = []

    def create_request(
        self, employee_id: int, employee_role: Role, lead_id: int
    ) -> object | None:
        self.create_calls.append((employee_id, employee_role, lead_id))
        return self.create_result


class FakeTasksService:
    def __init__(
        self,
        tasks: list[TaskRecord] | None = None,
        *,
        update_returns_none: bool = False,
    ):
        self.tasks = {task.task_id: task for task in (tasks or [])}
        self.update_returns_none = update_returns_none
        self.list_calls: list[tuple[int, set[str] | None]] = []
        self.completed_calls: list[tuple[int, str]] = []
        self.in_process_calls: list[int] = []
        self.get_calls: list[str] = []
        self.update_calls: list[tuple[str, str]] = []

    @staticmethod
    def _date_part(value: str) -> str:
        return str(value or "").strip()[:10]

    def list_tasks_assigned_to(
        self, employee_id: int, statuses: set[str] | None = None
    ) -> list[TaskRecord]:
        self.list_calls.append((employee_id, statuses))
        tasks = [
            task for task in self.tasks.values() if task.employee_id == employee_id
        ]
        if statuses is not None:
            allowed = {status.strip().lower() for status in statuses}
            tasks = [
                task for task in tasks if (task.status or "").strip().lower() in allowed
            ]
        return tasks

    def list_completed_tasks_for_date(
        self, employee_id: int, report_date: str
    ) -> list[TaskRecord]:
        self.completed_calls.append((employee_id, report_date))
        return list(
            reversed(
                [
                    task
                    for task in self.tasks.values()
                    if task.employee_id == employee_id
                    and (task.status or "").strip().lower()
                    in {"finished", "on consideration"}
                    and self._date_part(task.updated_at) == report_date
                ]
            )
        )

    def list_in_process_tasks(self, employee_id: int) -> list[TaskRecord]:
        self.in_process_calls.append(employee_id)
        return self.list_tasks_assigned_to(employee_id, {"in process"})

    def get_task_by_id(self, task_id: str) -> TaskRecord | None:
        self.get_calls.append(task_id)
        return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, new_status: str) -> TaskRecord | None:
        self.update_calls.append((task_id, new_status))
        if self.update_returns_none:
            return None
        task = self.tasks.get(task_id)
        if task is None:
            return None
        updated = replace(task, status=new_status, updated_at="2026-01-02 10:00:00")
        self.tasks[task_id] = updated
        return updated


class FakeReportsService:
    def __init__(self, *, feedback_by_task: dict[str, str] | None = None):
        self.feedback_by_task = feedback_by_task or {}
        self.created_reports: list[tuple[str, int, str]] = []

    def get_manager_feedback_by_task_id(self, task_id: str) -> str:
        return self.feedback_by_task.get(task_id, "")

    def create_report(self, task_id: str, employee_id: int, text: str) -> str:
        self.created_reports.append((task_id, employee_id, text))
        return f"report-{task_id}"


class FakeAcceptedTasksService:
    def __init__(
        self, *, titles_by_key: dict[tuple[int, str], list[str]] | None = None
    ):
        self.titles_by_key = titles_by_key or {}
        self.title_calls: list[tuple[int, str]] = []

    def list_task_titles_for_employee_on_date(
        self, employee_id: int, report_date: str
    ) -> list[str]:
        self.title_calls.append((employee_id, report_date))
        return list(self.titles_by_key.get((employee_id, report_date), []))


class FakeDailyReportsService:
    def __init__(
        self,
        reports: list[DailyReportRecord] | None = None,
        *,
        today: str = "2026-05-17",
        was_updated: bool = False,
        missing_count: int | None = None,
    ):
        self.reports = reports or []
        self.today = today
        self.was_updated = was_updated
        self.missing_count = missing_count
        self.create_calls: list[tuple[int, str, str, str, list[str], list[str]]] = []
        self.list_calls: list[tuple[str, list[int] | None]] = []
        self.missing_calls: list[tuple[int, list[Any]]] = []

    def today_str(self) -> str:
        return self.today

    def create_or_update_report(
        self,
        employee_id: int,
        report_date: str,
        work_done: str,
        problems: str,
        completed_tasks_titles: list[str],
        in_process_tasks_titles: list[str],
    ) -> tuple[str, bool]:
        self.create_calls.append(
            (
                employee_id,
                report_date,
                work_done,
                problems,
                list(completed_tasks_titles),
                list(in_process_tasks_titles),
            )
        )
        return "daily-report-id", self.was_updated

    def list_reports_for_date(
        self, report_date: str, employee_ids: list[int] | None = None
    ) -> list[DailyReportRecord]:
        self.list_calls.append(
            (report_date, list(employee_ids) if employee_ids is not None else None)
        )
        allowed = set(employee_ids) if employee_ids is not None else None
        return [
            report
            for report in self.reports
            if report.report_date == report_date
            and (allowed is None or report.employee_id in allowed)
        ]

    def count_missing_reports_for_employee_between(self, employee_id: int, report_dates) -> int:
        dates = list(report_dates)
        self.missing_calls.append((employee_id, dates))
        if self.missing_count is not None:
            return self.missing_count
        available_dates = {report.report_date for report in self.reports if report.employee_id == employee_id}
        return sum(1 for report_date in dates if report_date.isoformat() not in available_dates)


class FakeTaskRequestService:
    def __init__(self):
        self.create_calls: list[tuple[str, str, list[int], int]] = []

    def create_requests(
        self, title: str, description: str, manager_ids: list[int], author_id: int
    ) -> int:
        self.create_calls.append((title, description, list(manager_ids), author_id))
        return len(set(manager_ids))


def make_task(
    task_id: str = "task-1",
    *,
    employee_id: int | None = 100,
    author_id: int | None = 200,
    status: str = "created",
    title: str = "Задача",
    description: str = "Описание",
    deadline: str = "2026-12-31",
    created_at: str = "2026-01-01 09:00:00",
    updated_at: str = "2026-01-01 09:00:00",
) -> TaskRecord:
    return TaskRecord(
        row_index=2,
        task_id=task_id,
        title=title,
        description=description,
        employee_id=employee_id,
        author_id=author_id,
        status=status,
        created_at=created_at,
        updated_at=updated_at,
        deadline=deadline,
    )


class FakeAuthUser:
    def __init__(self, tg_id: int, roles: list[Role]):
        self.tg_id = tg_id
        self.roles = roles


class FakeSuperuserAuthService:
    def __init__(
        self,
        *,
        users: list[FakeAuthUser] | None = None,
        can_superuser: dict[int, bool] | None = None,
        revoke_map: dict[tuple[int, Role], bool] | None = None,
        roles_after_revoke: dict[int, list[Role]] | None = None,
        banned_ids: list[int] | None = None,
        ban_result: bool = True,
        unban_result: bool = True,
    ):
        self.users = users or []
        self.can_superuser = can_superuser or {}
        self.revoke_map = revoke_map or {}
        self.roles_after_revoke = roles_after_revoke or {}
        self._banned_ids: list[int] = list(banned_ids or [])
        self.ban_result = ban_result
        self.unban_result = unban_result

        self.revoke_calls: list[tuple[int, Role]] = []
        self.get_user_roles_calls: list[int] = []
        self.ban_calls: list[int] = []
        self.unban_calls: list[int] = []

    def get_all_users(self) -> list[FakeAuthUser]:
        return list(self.users)

    def can_login_as_role(self, tg_id: int, role: Role) -> bool:
        if role == Role.SUPERUSER:
            return self.can_superuser.get(tg_id, False)
        return True

    def revoke_role(self, tg_id: int, role: Role) -> bool:
        self.revoke_calls.append((tg_id, role))
        return self.revoke_map.get((tg_id, role), False)

    def get_user_roles(self, tg_id: int) -> list[Role]:
        self.get_user_roles_calls.append(tg_id)
        return list(self.roles_after_revoke.get(tg_id, []))

    def is_banned(self, tg_id: int) -> bool:
        return tg_id in self._banned_ids

    def ban_user(self, tg_id: int) -> bool:
        self.ban_calls.append(tg_id)
        if self.ban_result:
            self._banned_ids.append(tg_id)
        return self.ban_result

    def unban_user(self, tg_id: int) -> bool:
        self.unban_calls.append(tg_id)
        if self.unban_result and tg_id in self._banned_ids:
            self._banned_ids.remove(tg_id)
        return self.unban_result

    def get_banned_users(self) -> list[int]:
        return list(self._banned_ids)

    def logout(self, tg_id: int) -> None:
        pass


class FakeRoleRequestService:
    def __init__(
        self,
        *,
        requests: list[dict[str, str]] | None = None,
        approve_map: dict[tuple[int, str], bool] | None = None,
        deny_map: dict[tuple[int, str], bool] | None = None,
    ):
        self.requests = requests or []
        self.approve_map = approve_map or {}
        self.deny_map = deny_map or {}

        self.get_calls = 0
        self.approve_calls: list[tuple[int, Role]] = []
        self.deny_calls: list[tuple[int, Role]] = []

    def get_all_requests(self) -> list[dict[str, str]]:
        self.get_calls += 1
        return list(self.requests)

    def approve_request(self, tg_id: int, role: Role, _auth_service: Any) -> bool:
        self.approve_calls.append((tg_id, role))
        return self.approve_map.get((tg_id, role.value), False)

    def deny_request(self, tg_id: int, role: Role) -> bool:
        self.deny_calls.append((tg_id, role))
        return self.deny_map.get((tg_id, role.value), False)


class FakeLeadState(FakeState):
    async def get_state(self):
        return self.state


class FakeLeadBot(FakeBot):
    def __init__(self, chats: dict[int, object] | None = None):
        super().__init__(chats)
        self.deleted_messages: list[tuple[int, int]] = []
        self.sent_messages: list[tuple[int, str]] = []

    async def delete_message(self, chat_id: int, message_id: int) -> None:
        self.deleted_messages.append((chat_id, message_id))

    async def send_message(self, chat_id: int, text: str, **_kwargs: Any) -> None:
        self.sent_messages.append((chat_id, text))


class FakeLeadMessage(FakeMessage):
    def __init__(self, **kwargs: Any):
        super().__init__(**kwargs)
        self.deleted = False

    async def delete(self) -> None:
        self.deleted = True


class FakeLeadAuthService:
    def __init__(
        self, *, team: list[int] | None = None, add_manager_result: bool = True
        self,
        *,
        team: list[int] | None = None,
        add_manager_result: bool = True,
        notification_settings: dict[int, dict[str, str]] | None = None,
    ):
        self.team = team or []
        self.add_manager_result = add_manager_result
        self.notification_settings = notification_settings or {}
        self.add_manager_calls: list[tuple[int, Role, int]] = []

    def get_team_members_for_manager(self, lead_id: int) -> list[int]:
        return list(self.team)

    def add_manager_for_user(
        self, employee_id: int, employee_role: Role, lead_id: int
    ) -> bool:
    def get_notification_settings(self, tg_id: int, default_morning_time: str, default_evening_time: str, default_timezone: str) -> dict[str, str]:
        return dict(self.notification_settings.get(tg_id, {
            "morning_time": default_morning_time,
            "evening_time": default_evening_time,
            "timezone": default_timezone,
        }))

    def add_manager_for_user(self, employee_id: int, employee_role: Role, lead_id: int) -> bool:
        self.add_manager_calls.append((employee_id, employee_role, lead_id))
        return self.add_manager_result


class FakeLeadVisitsService:
    def __init__(
        self,
        *,
        start_result: bool = True,
        finish_result: bool = True,
        worked_hours: float = 0,
    ):
        self.start_result = start_result
        self.finish_result = finish_result
        self.worked_hours = worked_hours
        self.start_calls: list[int] = []
        self.finish_calls: list[int] = []
        self.hours_calls: list[tuple[Any, ...]] = []

    def start_workday(self, tg_id: int) -> bool:
        self.start_calls.append(tg_id)
        return self.start_result

    def finish_workday(self, tg_id: int) -> bool:
        self.finish_calls.append(tg_id)
        return self.finish_result

    def sum_worked_hours_for_employee_between(self, employee_id, start_date, end_date):
        self.hours_calls.append((employee_id, start_date, end_date))
        return self.worked_hours


class FakeLeadTasksService:
    def __init__(self, tasks=None, *, create_error: Exception | None = None):
        self.tasks = {task.task_id: task for task in (tasks or [])}
        self.create_error = create_error
        self.created_tasks: list[tuple[Any, ...]] = []
        self.deleted_task_ids: list[str] = []
        self.status_updates: list[tuple[str, str]] = []
        self.get_all_calls = 0

    def get_all_tasks(self):
        self.get_all_calls += 1
        return list(self.tasks.values())

    def list_tasks_created_by(self, author_id: int):
        return [task for task in self.tasks.values() if task.author_id == author_id]

    def get_task_by_id(self, task_id: str):
        return self.tasks.get(task_id)

    def create_task_created(self, *args: Any):
        if self.create_error:
            raise self.create_error
        self.created_tasks.append(args)
        return "created-task-id"

    def delete_task_by_id(self, task_id: str):
        self.deleted_task_ids.append(task_id)
        self.tasks.pop(task_id, None)

    def update_task_status(self, task_id: str, new_status: str):
        self.status_updates.append((task_id, new_status))
        task = self.tasks.get(task_id)
        if task:
            self.tasks[task_id] = replace(task, status=new_status)
            return self.tasks[task_id]
        return None


class FakeLeadReportsService:
    def __init__(self, reports=None):
        self.reports = {report.task_id: report for report in (reports or [])}
        self.deleted_report_task_ids: list[str] = []
        self.feedback_updates: list[tuple[str, str]] = []

    def get_all_reports(self):
        return list(self.reports.values())

    def get_report_by_task_id(self, task_id: str):
        return self.reports.get(task_id)

    def delete_report_by_task_id(self, task_id: str):
        self.deleted_report_task_ids.append(task_id)
        self.reports.pop(task_id, None)

    def update_manager_feedback(self, task_id: str, comment: str):
        self.feedback_updates.append((task_id, comment))


class FakeLeadAcceptedTasksService:
    def __init__(self, records: list[AcceptedTaskRecord] | None = None):
        self.records = records or []
        self.accepted: list[tuple[ReportRecord, Any, str]] = []
        self.get_all_calls = 0

    def get_all_records(self):
        self.get_all_calls += 1
        return list(self.records)

    def create_from_report(self, report: ReportRecord, task: Any, comment: str):
        self.accepted.append((report, task, comment))


class FakeLeadTaskRequestService:
    def __init__(self, requests=None):
        self.requests = {
            request.callback_token: request for request in (requests or [])
        }
        self.deleted: list[str] = []
        self.deleted_related: list[str] = []

    def list_requests_for_lead(self, lead_id: int):
        return [req for req in self.requests.values() if req.lead_id == lead_id]

    def get_request_for_lead_by_token(self, token: str, lead_id: int):
        req = self.requests.get(token)
        return req if req and req.lead_id == lead_id else None

    def delete_request(self, request: TaskRequestRecord):
        self.deleted.append(request.callback_token)
        self.requests.pop(request.callback_token, None)

    def delete_related_requests(self, request: TaskRequestRecord):
        self.deleted_related.append(request.callback_token)
        self.requests.pop(request.callback_token, None)


class FakeLeadManagerBindingService:
    def __init__(self, requests=None):
        self.requests = {request.request_id: request for request in (requests or [])}
        self.deleted: list[str] = []

    def list_requests_for_lead(self, lead_id: int):
        return [req for req in self.requests.values() if req.lead_id == lead_id]

    def get_request_by_id(self, request_id: str, lead_id: int):
        req = self.requests.get(request_id)
        return req if req and req.lead_id == lead_id else None

    def delete_request(self, request_id: str):
        self.deleted.append(request_id)
        self.requests.pop(request_id, None)


def make_report(
    task_id: str = "task-1", *, employee_id: int = 100, text: str = "Готово"
) -> ReportRecord:
    return ReportRecord(
        2, f"report-{task_id}", task_id, employee_id, text, "2026-01-02", {}
    )

def make_accepted_task(
    report_id: str = "report-task-1",
    *,
    employee_id: int = 100,
    date_value: str = "2026-05-18 18:00:00",
    task_title: str = "Закрытая задача",
    description: str = "Описание закрытой задачи",
    status: str = "accepted",
    deadline: str = "2026-05-20",
    closed_at: str = "2026-05-18 18:00:00",
    assigned_at: str = "2026-05-17 09:00:00",
) -> AcceptedTaskRecord:
    return AcceptedTaskRecord(
        row_index=2,
        report_id=report_id,
        employee_id=employee_id,
        date_value=date_value,
        task_title=task_title,
        description=description,
        problems="",
        status=status,
        manager_feedback="",
        deadline=deadline,
        closed_at=closed_at,
        assigned_at=assigned_at,
    )


def make_report(task_id: str = "task-1", *, employee_id: int = 100, text: str = "Готово") -> ReportRecord:
    return ReportRecord(2, f"report-{task_id}", task_id, employee_id, text, "2026-01-02", {})

def make_request(
    token: str = "offer-1", *, lead_id: int = 200, author_id: int = 100
) -> TaskRequestRecord:
    return TaskRequestRecord(
        2, token, "Предложение", "Описание", lead_id, author_id, "new", "2026-01-01"
    )


def make_bind_request(
    request_id: str = "bind-1", *, lead_id: int = 200, employee_id: int = 100
) -> ManagerBindRequest:
    return ManagerBindRequest(
        request_id, employee_id, Role.EMPLOYEE, lead_id, "2026-01-01"
    )


def make_daily_report(
    report_id: str = "daily-1",
    *,
    employee_id: int = 100,
    report_date: str = "2026-05-17",
    work_done: str = "Работа",
    problems: str = "Проблемы",
    completed_tasks_count: int = 1,
    completed_tasks_titles: str = "Готовая задача",
    in_process_tasks_count: int = 1,
    in_process_tasks_titles: str = "Текущая задача",
    created_at: str = "2026-05-17 18:00:00",
) -> DailyReportRecord:
    return DailyReportRecord(
        row_index=2,
        report_id=report_id,
        employee_id=employee_id,
        report_date=report_date,
        work_done=work_done,
        problems=problems,
        completed_tasks_count=completed_tasks_count,
        completed_tasks_titles=completed_tasks_titles,
        in_process_tasks_count=in_process_tasks_count,
        in_process_tasks_titles=in_process_tasks_titles,
        created_at=created_at,
        raw_fields={},
    )
