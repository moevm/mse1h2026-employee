from __future__ import annotations

from dataclasses import replace
from typing import Any

from roles import Role
from services.tasks_service import TaskRecord


class FakeVisitsService:
    def __init__(self, *, start_result: bool = True, finish_result: bool = True, open_visit: bool = False):
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

    def get_manager_ids_for_user(self, tg_id: int, role: Role | None = None) -> list[int]:
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

    def create_request(self, employee_id: int, employee_role: Role, lead_id: int) -> object | None:
        self.create_calls.append((employee_id, employee_role, lead_id))
        return self.create_result


class FakeTasksService:
    def __init__(self, tasks: list[TaskRecord] | None = None, *, update_returns_none: bool = False):
        self.tasks = {task.task_id: task for task in (tasks or [])}
        self.update_returns_none = update_returns_none
        self.list_calls: list[int] = []
        self.get_calls: list[str] = []
        self.update_calls: list[tuple[str, str]] = []

    def list_tasks_assigned_to(self, employee_id: int) -> list[TaskRecord]:
        self.list_calls.append(employee_id)
        return [task for task in self.tasks.values() if task.employee_id == employee_id]

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


class FakeTaskRequestService:
    def __init__(self):
        self.create_calls: list[tuple[str, str, list[int], int]] = []

    def create_requests(self, title: str, description: str, manager_ids: list[int], author_id: int) -> int:
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
) -> TaskRecord:
    return TaskRecord(
        row_index=2,
        task_id=task_id,
        title=title,
        description=description,
        employee_id=employee_id,
        author_id=author_id,
        status=status,
        created_at="2026-01-01 09:00:00",
        updated_at="2026-01-01 09:00:00",
        deadline=deadline,
    )

class FakeAuthUser:
    def __init__(self, tg_id: int, roles: list[Role]):
        self.tg_id = tg_id
        self.roles = roles

class FakeSuperuserAuthService:
    def __init__(self, *,
        users: list[FakeAuthUser] | None = None,
        can_superuser: dict[int, bool] | None = None,
        revoke_map: dict[tuple[int, Role], bool] | None = None,
        roles_after_revoke: dict[int, list[Role]] | None = None,
    ):
        self.users = users or []
        self.can_superuser = can_superuser or {}
        self.revoke_map = revoke_map or {}
        self.roles_after_revoke = roles_after_revoke or {}

        self.revoke_calls: list[tuple[int, Role]] = []
        self.get_user_roles_calls: list[int] = []

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
