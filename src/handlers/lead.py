import asyncio
import logging
import re
from datetime import date, timedelta
from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants.bot_constants import Buttons
from constants.texts import (
    ACTION_CANCELLED_TEXT,
    LEAD_CREATE_TASK_DEADLINE_PROMPT,
    LEAD_CREATE_TASK_DEADLINE_SELECTED,
    LEAD_CREATE_TASK_DESCRIPTION_PROMPT,
    LEAD_CREATE_TASK_INVALID_EMPLOYEE_TEXT,
    LEAD_CREATE_TASK_NO_EMPLOYEES_TEXT,
    LEAD_CREATE_TASK_SELECT_EMPLOYEE_PROMPT,
    LEAD_CREATE_TASK_SUCCESS,
    LEAD_CREATE_TASK_TITLE_PROMPT,
    LEAD_MENU_TEXT,
    LEAD_BIND_REQUESTS_EMPTY_TEXT,
    LEAD_BIND_REQUEST_ACCEPTED_TEXT,
    LEAD_BIND_REQUEST_REJECTED_TEXT,
    LEAD_BIND_REQUEST_NOT_FOUND_TEXT,
    LEAD_REPORT_NOT_FOUND_TEXT,
    LEAD_REPORTS_EMPTY_TEXT,
    LEAD_REPORTS_LIST_TEXT,
    LEAD_REPORTS_TEXT,
    LEAD_DAILY_REPORTS_EMPTY_TEXT,
    LEAD_DAILY_REPORTS_OUT_OF_RANGE_TEXT,
    LEAD_DAILY_REPORTS_SELECTED_DATE_TEXT,
    LEAD_DAILY_REPORTS_SELECT_DATE_TEXT,
    LEAD_TASKS_EMPTY_TEXT,
    LEAD_TASK_PROPOSAL_ACCEPT_DEADLINE_PROMPT,
    LEAD_TASK_PROPOSAL_ACCEPT_SUCCESS,
    LEAD_TASK_PROPOSAL_NOT_FOUND_TEXT,
    LEAD_TASK_PROPOSAL_REJECT_SUCCESS,
    LEAD_TASK_PROPOSALS_EMPTY_TEXT,
    LEAD_TASK_PROPOSALS_LIST_TEXT,
    LEAD_TASKS_LIST_TEXT,
    LEAD_TASKS_TEXT,
    LEAD_VIEW_REPORT_SUCCESS,
    LEAD_WEEKLY_TEXT,
    LEAD_WEEKLY_PERIOD_TEXT,
    LEAD_WEEKLY_NO_EMPLOYEES_TEXT,
    LEAD_WEEKLY_INVALID_EMPLOYEE_TEXT,
    LEAD_WEEKLY_INVALID_PERIOD_TEXT,
    LEAD_WEEKLY_RESULT_TEXT,
    TASK_NOT_FOUND_TEXT,
    VISIT_FINISH_NO_OPEN_TEXT,
    VISIT_FINISH_SUCCESS_TEXT,
    VISIT_START_ALREADY_OPEN_TEXT,
    VISIT_START_SUCCESS_TEXT,
    LEAD_REJECT_REPORT_PROMPT,
    LEAD_REJECT_REPORT_SUCCESS,
    LEAD_REJECT_COMMENT_EMPTY,
    LEAD_ACCEPT_REPORT_COMMENT_QUESTION,
    LEAD_ACCEPT_REPORT_COMMENT_PROMPT,
    LEAD_ACCEPT_REPORT_SUCCESS,
    LEAD_ACCEPT_REPORT_WITH_COMMENT_SUCCESS,
)
from filters.active_role import ActiveRoleFilter
from handlers.common import resolve_user_label
from keyboards.inline_calendar import CAL_PREFIX, build_calendar, calendar_for_today, calendar_for_range
from keyboards.role_menus import (
    LEAD_REPORT_CALLBACK_PREFIX,
    TASK_PROPOSAL_CALLBACK_PREFIX,
    MANAGER_BIND_CALLBACK_PREFIX,
    get_employee_selection_keyboard,
    get_lead_accept_comment_choice_keyboard,
    get_lead_cancel_keyboard,
    get_lead_main_keyboard,
    get_lead_report_item_keyboard,
    get_lead_reports_keyboard,
    get_lead_tasks_keyboard,
    get_task_proposal_action_keyboard,
    get_manager_bind_action_keyboard,
    get_week_period_selection_keyboard,
)
from roles import Role
from services.accepted_tasks_service import AcceptedTasksService
from services.auth_service import AuthService
from services.reports_service import ReportRecord, ReportsService
from services.daily_reports_service import DailyReportRecord, DailyReportsService
from services.manager_binding_service import ManagerBindingService, ManagerBindRequest
from services.task_request_service import TaskRequestRecord, TaskRequestService
from services.tasks_service import TaskRecord, TasksService, format_task_for_lead
from services.visits_service import VisitsService
from states.lead import LeadStates

logger = logging.getLogger(__name__)


def format_report_summary_for_lead(task: TaskRecord, employee_label: str) -> str:
    safe_title = escape(task.title) if task.title else "—"
    safe_employee_label = escape(employee_label) if employee_label else "—"
    return (
        f"<b>Название задачи:</b> {safe_title}\n"
        f"<b>Тег выполнившего сотрудника:</b> {safe_employee_label}"
    )


def format_report_details_for_lead(task: TaskRecord, employee_label: str, report: ReportRecord) -> str:
    safe_title = escape(task.title) if task.title else "—"
    safe_employee_label = escape(employee_label) if employee_label else "—"
    safe_text = escape(report.text) if report.text else "—"
    return (
        f"<b>Название задачи:</b> {safe_title}\n"
        f"<b>Тег выполнившего сотрудника:</b> {safe_employee_label}\n"
        f"<b>Содержимое отчета:</b>\n{safe_text}"
    )


def _safe_multiline(value: str) -> str:
    value = str(value or "").strip()
    return escape(value) if value else "—"


def format_daily_report_for_lead(report: DailyReportRecord, employee_label: str) -> str:
    safe_employee_label = escape(employee_label) if employee_label else "—"
    safe_date = escape(report.report_date) if report.report_date else "—"
    work_done = _safe_multiline(report.work_done)
    problems = _safe_multiline(report.problems)
    completed_titles = _safe_multiline(report.completed_tasks_titles)
    in_process_titles = _safe_multiline(report.in_process_tasks_titles)

    return (
        f"<b>Сотрудник:</b> {safe_employee_label}\n"
        f"<b>Дата:</b> {safe_date}\n\n"
        f"<b>Какая работа была проделана:</b>\n{work_done}\n\n"
        f"<b>С какими проблемами пришлось столкнуться:</b>\n{problems}\n\n"
        f"<b>Выполненныx задач за день:</b> {report.completed_tasks_count}\n"
        f"{completed_titles}\n\n"
        f"<b>Задач в процессе:</b> {report.in_process_tasks_count}\n"
        f"{in_process_titles}"
    )


def _daily_report_date_bounds(today: date) -> tuple[date, date]:
    return today - timedelta(days=365), today


def _parse_days_of_week(value: str) -> set[int]:
    mapping = {
        "mon": 0,
        "tue": 1,
        "wed": 2,
        "thu": 3,
        "fri": 4,
        "sat": 5,
        "sun": 6,
    }
    result: set[int] = set()
    for day in str(value or "").split(","):
        normalized_day = day.strip().lower()
        if normalized_day in mapping:
            result.add(mapping[normalized_day])
    return result or {0, 1, 2, 3, 4}


def _current_week_bounds(today: date) -> tuple[date, date]:
    week_start = today - timedelta(days=today.weekday())
    return week_start, today


def _work_dates_between(start_date: date, end_date: date, allowed_weekdays: set[int]) -> list[date]:
    dates: list[date] = []
    current = start_date
    while current <= end_date:
        if current.weekday() in allowed_weekdays:
            dates.append(current)
        current += timedelta(days=1)
    return dates


def _format_hours(value: float | int) -> str:
    rounded_value = round(float(value), 2)
    if rounded_value.is_integer():
        return str(int(rounded_value))
    return f"{rounded_value:.2f}".rstrip("0").rstrip(".")


def _date_part(value: str) -> str:
    value = str(value or "").strip()
    match = re.search(r"\d{4}-\d{2}-\d{2}", value)
    if match:
        return match.group(0)
    return value


def _parse_date_value(value: str) -> date | None:
    value = _date_part(value)
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _is_closed_task_status(status: str) -> bool:
    return (status or "accepted").strip().lower() in {"accepted", "closed", "done", "finished"}


def _is_open_task_status(status: str) -> bool:
    return (status or "").strip().lower() not in {"accepted", "closed", "done"}


def _accepted_task_closed_date(record) -> date | None:
    return _parse_date_value(getattr(record, "closed_at", "") or getattr(record, "date_value", ""))


def _task_created_date(task: TaskRecord) -> date | None:
    return _parse_date_value(getattr(task, "created_at", ""))


def _task_deadline_date(task) -> date | None:
    return _parse_date_value(getattr(task, "deadline", ""))


def _build_week_period_options(today: date) -> dict[str, tuple[str, str]]:
    current_start = today - timedelta(days=today.weekday())
    options: dict[str, tuple[str, str]] = {}

    for offset in range(5):
        if offset == 0:
            start_date, end_date = current_start, today
            label = "Текущая неделя"
        else:
            start_date = current_start - timedelta(days=7 * offset)
            end_date = start_date + timedelta(days=6)
            label = f"{offset} неделя назад"

        button_text = f"{label}: {start_date.strftime('%d.%m.%Y')} — {end_date.strftime('%d.%m.%Y')}"
        options[button_text] = (start_date.isoformat(), end_date.isoformat())

    return options


def _format_date_for_report(value: str) -> str:
    parsed = _parse_date_value(value)
    if parsed is not None:
        return parsed.isoformat()
    return str(value).strip() if str(value).strip() else "—"


def _task_assignment_date_value(item: object) -> str:
    return (
        getattr(item, "assigned_at", "")
        or getattr(item, "created_at", "")
        or ""
    )


def _task_closed_date_value(item: object) -> str:
    return (
        getattr(item, "closed_at", "")
        or getattr(item, "date_value", "")
        or ""
    )


def _format_task_items(
    items: list[object],
    *,
    include_deadline: bool = False,
    include_assignment_date: bool = False,
    include_closed_date: bool = False,
) -> str:
    if not items:
        return "—"

    lines: list[str] = []
    for index, item in enumerate(items, start=1):
        title = (getattr(item, "task_title", "") or getattr(item, "title", "") or "—")
        description = (getattr(item, "description", "") or "—")
        item_lines = [
            f"{index}. <b>{escape(str(title))}</b>",
            f"   Описание: {escape(str(description))}",
        ]
        if include_assignment_date:
            item_lines.append(f"   Дата назначения: {escape(_format_date_for_report(_task_assignment_date_value(item)))}")
        if include_closed_date:
            item_lines.append(f"   Дата закрытия: {escape(_format_date_for_report(_task_closed_date_value(item)))}")
        if include_deadline:
            deadline = getattr(item, "deadline", "") or "—"
            item_lines.append(f"   Дедлайн: {escape(_format_date_for_report(str(deadline)))}")
        lines.append("\n".join(item_lines))
    return "\n".join(lines)


def _build_weekly_report_stats(
    accepted_tasks_service: AcceptedTasksService,
    tasks_service: TasksService,
    visits_service: VisitsService,
    daily_reports_service: DailyReportsService,
    employee_id: int,
    week_start: date,
    week_end: date,
    work_dates: list[date],
    today: date,
) -> dict[str, object]:
    accepted_records_loaded = hasattr(accepted_tasks_service, "get_all_records")
    if accepted_records_loaded:
        accepted_records = accepted_tasks_service.get_all_records()
    else:
        accepted_records = []

    closed_tasks = []
    closed_overdue_tasks = []
    for record in accepted_records:
        if getattr(record, "employee_id", None) != employee_id:
            continue
        if not _is_closed_task_status(getattr(record, "status", "accepted")):
            continue

        closed_date = _accepted_task_closed_date(record)
        if closed_date is not None and week_start <= closed_date <= week_end:
            closed_tasks.append(record)

        deadline = _parse_date_value(getattr(record, "deadline", ""))
        if (
            deadline is not None
            and week_start <= deadline <= week_end
            and closed_date is not None
            and closed_date > deadline
        ):
            closed_overdue_tasks.append(record)

    if not accepted_records_loaded and hasattr(accepted_tasks_service, "list_closed_tasks_for_employee_between"):
        closed_tasks = accepted_tasks_service.list_closed_tasks_for_employee_between(employee_id, week_start, week_end)
        closed_overdue_tasks = []
        if hasattr(accepted_tasks_service, "list_closed_overdue_tasks_for_employee_between"):
            closed_overdue_tasks = accepted_tasks_service.list_closed_overdue_tasks_for_employee_between(
                employee_id,
                week_start,
                week_end,
            )

    active_tasks_loaded = hasattr(tasks_service, "get_all_tasks")
    if active_tasks_loaded:
        active_tasks = tasks_service.get_all_tasks()
    else:
        active_tasks = []

    assigned_tasks = []
    open_overdue_tasks = []
    overdue_reference_date = min(week_end, today)
    for task in active_tasks:
        if getattr(task, "employee_id", None) != employee_id:
            continue

        created_date = _task_created_date(task)
        if created_date is not None and week_start <= created_date <= week_end:
            assigned_tasks.append(task)

        deadline = _task_deadline_date(task)
        if deadline is None or not (week_start <= deadline <= week_end):
            continue
        if deadline > overdue_reference_date:
            continue
        if created_date is not None and created_date > overdue_reference_date:
            continue
        if _is_open_task_status(getattr(task, "status", "")):
            open_overdue_tasks.append(task)

    if not active_tasks_loaded:
        if hasattr(tasks_service, "list_tasks_assigned_to_between"):
            assigned_tasks = tasks_service.list_tasks_assigned_to_between(employee_id, week_start, week_end)
        if hasattr(tasks_service, "list_open_overdue_tasks_for_employee_between"):
            open_overdue_tasks = tasks_service.list_open_overdue_tasks_for_employee_between(
                employee_id,
                week_start,
                overdue_reference_date,
            )
        elif hasattr(tasks_service, "list_open_overdue_tasks_for_employee"):
            open_overdue_tasks = [
                task
                for task in tasks_service.list_open_overdue_tasks_for_employee(employee_id, overdue_reference_date)
                if (deadline := _task_deadline_date(task)) is not None and week_start <= deadline <= week_end
            ]

    worked_hours = _sum_worked_hours(visits_service, employee_id, week_start, week_end)
    missing_daily_reports_count = _count_missing_daily_reports(daily_reports_service, employee_id, work_dates)

    return {
        "closed_tasks": list(reversed(closed_tasks)),
        "assigned_tasks": list(reversed(assigned_tasks)),
        "overdue_tasks": list(reversed(closed_overdue_tasks)) + list(reversed(open_overdue_tasks)),
        "worked_hours": worked_hours,
        "missing_daily_reports_count": missing_daily_reports_count,
    }


def _count_missing_daily_reports(daily_reports_service: DailyReportsService, employee_id: int, report_dates: list[date]) -> int:
    if hasattr(daily_reports_service, "count_missing_reports_for_employee_between"):
        return daily_reports_service.count_missing_reports_for_employee_between(employee_id, report_dates)

    missing_count = 0
    for report_date in report_dates:
        normalized_date = report_date.isoformat()
        if hasattr(daily_reports_service, "get_report_for_employee_date"):
            report = daily_reports_service.get_report_for_employee_date(employee_id, normalized_date)
            if report is None:
                missing_count += 1
            continue

        reports = daily_reports_service.list_reports_for_date(normalized_date, [employee_id])
        if not reports:
            missing_count += 1
    return missing_count



def _sum_worked_hours(visits_service: VisitsService, employee_id: int, start_date: date, end_date: date) -> float:
    if hasattr(visits_service, "sum_worked_hours_for_employee_between"):
        return visits_service.sum_worked_hours_for_employee_between(employee_id, start_date, end_date)
    return 0.0


async def _build_employee_options(bot, employee_ids: list[int]) -> dict[str, int]:
    options: dict[str, int] = {}
    for employee_id in employee_ids:
        label = await resolve_user_label(bot, employee_id)
        button_label = label
        if button_label in options:
            button_label = f"{label} (ID: {employee_id})"
        options[button_label] = employee_id
    return options


def format_task_proposal_for_lead(request: TaskRequestRecord, employee_label: str) -> str:
    safe_title = escape(request.title) if request.title else "—"
    safe_description = escape(request.description) if request.description else "—"
    safe_employee_label = escape(employee_label) if employee_label else "—"
    safe_created_at = escape(request.created_at) if request.created_at else "—"

    return (
        f"<b>Название:</b> {safe_title}\n"
        f"<b>Описание:</b> {safe_description}\n"
        f"<b>Предложил:</b> {safe_employee_label}\n"
        f"<b>Создано:</b> {safe_created_at}"
    )


def format_manager_bind_request_for_lead(request: ManagerBindRequest, employee_label: str) -> str:
    safe_employee_label = escape(employee_label) if employee_label else "—"
    safe_role = escape(request.employee_role.title)
    safe_created_at = escape(request.created_at) if request.created_at else "—"
    return (
        f"<b>Запрос на привязку руководителя</b>\n"
        f"<b>Пользователь:</b> {safe_employee_label}\n"
        f"<b>Роль:</b> {safe_role}\n"
        f"<b>Создано:</b> {safe_created_at}"
    )


def setup_lead_router(
    auth_service: AuthService,
    tasks_service: TasksService,
    visits_service: VisitsService,
    reports_service: ReportsService,
    accepted_tasks_service: AcceptedTasksService,
    task_request_service: TaskRequestService,
    manager_binding_service: ManagerBindingService,
    daily_reports_service: DailyReportsService | None = None,
    default_morning_time: str = "08:50",
    default_evening_time: str = "16:50",
    default_timezone: str = "Europe/Moscow",
    default_days_of_week: str = "mon,tue,wed,thu,fri",
):
    if daily_reports_service is None:
        from datetime import date as _date

        class _FallbackDailyReportsService:
            def today_str(self):
                return _date.today().isoformat()

            def list_reports_for_date(self, *_args, **_kwargs):
                return []

        daily_reports_service = _FallbackDailyReportsService()

    router = Router()
    router.message.filter(ActiveRoleFilter(auth_service, Role.LEAD))
    router.callback_query.filter(ActiveRoleFilter(auth_service, Role.LEAD))

    @router.message(F.text == Buttons.START_WORK)
    async def start_work(message: Message):
        success = visits_service.start_workday(message.from_user.id)

        if success:
            await message.answer(
                VISIT_START_SUCCESS_TEXT,
                reply_markup=get_lead_main_keyboard(),
            )
        else:
            await message.answer(
                VISIT_START_ALREADY_OPEN_TEXT,
                reply_markup=get_lead_main_keyboard(),
            )

    @router.message(F.text == Buttons.FINISH_WORK)
    async def finish_work(message: Message):
        success = visits_service.finish_workday(message.from_user.id)

        if success:
            await message.answer(
                VISIT_FINISH_SUCCESS_TEXT,
                reply_markup=get_lead_main_keyboard(),
            )
        else:
            await message.answer(
                VISIT_FINISH_NO_OPEN_TEXT,
                reply_markup=get_lead_main_keyboard(),
            )


    @router.message(F.text == Buttons.LEAD_BIND_REQUESTS)
    async def lead_bind_requests(message: Message, state: FSMContext):
        await state.clear()
        requests = await asyncio.to_thread(
            manager_binding_service.list_requests_for_lead,
            message.from_user.id,
        )

        if not requests:
            await message.answer(
                LEAD_BIND_REQUESTS_EMPTY_TEXT,
                reply_markup=get_lead_main_keyboard(),
            )
            return

        for request in requests:
            employee_label = await resolve_user_label(message.bot, request.employee_id)
            await message.answer(
                format_manager_bind_request_for_lead(request, employee_label),
                reply_markup=get_manager_bind_action_keyboard(request.request_id),
                parse_mode="HTML",
            )

    @router.callback_query(F.data.startswith(f"{MANAGER_BIND_CALLBACK_PREFIX}:"))
    async def lead_bind_request_action(callback: CallbackQuery):
        _, action, request_id = callback.data.split(":", 2)
        request = await asyncio.to_thread(
            manager_binding_service.get_request_by_id,
            request_id,
            callback.from_user.id,
        )

        if request is None:
            await callback.answer(LEAD_BIND_REQUEST_NOT_FOUND_TEXT, show_alert=True)
            return

        if action == "reject":
            employee_label = await resolve_user_label(callback.bot, request.employee_id)

            employee_label = await resolve_user_label(callback.bot, request.employee_id)



            await asyncio.to_thread(manager_binding_service.delete_request, request.request_id)
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer(
                LEAD_BIND_REQUEST_REJECTED_TEXT,
                reply_markup=get_lead_main_keyboard(),
            )
            await callback.answer()
            return

        if action == "accept":
            success = await asyncio.to_thread(
                auth_service.add_manager_for_user,
                request.employee_id,
                request.employee_role,
                callback.from_user.id,
            )
            if not success:
                await callback.answer(LEAD_BIND_REQUEST_NOT_FOUND_TEXT, show_alert=True)
                return

            employee_label = await resolve_user_label(callback.bot, request.employee_id)

            await asyncio.to_thread(manager_binding_service.delete_request, request.request_id)
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer(
                LEAD_BIND_REQUEST_ACCEPTED_TEXT.format(employee_label=employee_label),
                reply_markup=get_lead_main_keyboard(),
                parse_mode="HTML",
            )
            await callback.answer()
            return

        await callback.answer(LEAD_BIND_REQUEST_NOT_FOUND_TEXT, show_alert=True)

    @router.message(F.text == Buttons.LEAD_TASKS)
    async def lead_tasks_menu(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(LEAD_TASKS_TEXT, reply_markup=get_lead_tasks_keyboard())

    @router.message(F.text == Buttons.LEAD_REPORTS)
    async def lead_reports_menu(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(LEAD_REPORTS_TEXT, reply_markup=get_lead_reports_keyboard())


    @router.message(F.text == Buttons.LEAD_DAILY_REPORTS)
    async def lead_daily_reports_start(message: Message, state: FSMContext):
        await state.clear()
        await state.set_state(LeadStates.waiting_daily_report_date)
        await state.update_data(return_to="reports")

        today = date.fromisoformat(await asyncio.to_thread(daily_reports_service.today_str))
        min_date, max_date = _daily_report_date_bounds(today)

        await message.answer(
            LEAD_DAILY_REPORTS_SELECT_DATE_TEXT,
            reply_markup=calendar_for_range(min_date, max_date, today),
        )

    @router.callback_query(LeadStates.waiting_daily_report_date, F.data.startswith(f"{CAL_PREFIX}:"))
    async def lead_daily_reports_calendar(call: CallbackQuery, state: FSMContext):
        parts = call.data.split(":")
        action = parts[1]

        today = date.fromisoformat(await asyncio.to_thread(daily_reports_service.today_str))
        min_date, max_date = _daily_report_date_bounds(today)

        if action == "ignore":
            await call.answer()
            return

        if action == "cancel":
            await state.clear()
            await call.message.edit_text(ACTION_CANCELLED_TEXT)
            await call.message.answer(LEAD_REPORTS_TEXT, reply_markup=get_lead_reports_keyboard())
            await call.answer()
            return

        if action == "nav":
            year = int(parts[2])
            month = int(parts[3])
            await call.message.edit_text(
                LEAD_DAILY_REPORTS_SELECT_DATE_TEXT,
                reply_markup=build_calendar(year, month, min_date=min_date, max_date=max_date),
            )
            await call.answer()
            return

        if action != "pick":
            await call.answer()
            return

        selected_date = date(int(parts[2]), int(parts[3]), int(parts[4]))
        if selected_date < min_date or selected_date > max_date:
            await call.answer(LEAD_DAILY_REPORTS_OUT_OF_RANGE_TEXT, show_alert=True)
            return

        report_date = selected_date.strftime("%Y-%m-%d")
        employee_ids = await asyncio.to_thread(
            auth_service.get_team_members_for_manager,
            call.from_user.id,
        )
        daily_reports = await asyncio.to_thread(
            daily_reports_service.list_reports_for_date,
            report_date,
            employee_ids,
        )

        await state.clear()
        await call.message.edit_text(LEAD_DAILY_REPORTS_SELECTED_DATE_TEXT.format(date=report_date))

        if not daily_reports:
            await call.message.answer(
                LEAD_DAILY_REPORTS_EMPTY_TEXT,
                reply_markup=get_lead_reports_keyboard(),
            )
            await call.answer()
            return

        for report in daily_reports:
            employee_label = await resolve_user_label(call.bot, report.employee_id)
            await call.message.answer(
                format_daily_report_for_lead(report, employee_label),
                parse_mode="HTML",
            )

        await call.answer()

    @router.message(F.text == Buttons.LEAD_WEEKLY_REPORT)
    async def lead_weekly_start(message: Message, state: FSMContext):
        await state.clear()
        employee_ids = await asyncio.to_thread(
            auth_service.get_team_members_for_manager,
            message.from_user.id,
        )

        if not employee_ids:
            await message.answer(
                LEAD_WEEKLY_NO_EMPLOYEES_TEXT,
                reply_markup=get_lead_reports_keyboard(),
            )
            return

        employee_options = await _build_employee_options(message.bot, employee_ids)
        await state.set_state(LeadStates.waiting_weekly_user)
        await state.update_data(return_to="reports", weekly_employee_options=employee_options)
        await message.answer(
            LEAD_WEEKLY_TEXT,
            reply_markup=get_employee_selection_keyboard(list(employee_options.keys()), include_exit=False),
        )

    @router.message(F.text == Buttons.MAIN_MENU)
    async def lead_back_to_main(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(LEAD_MENU_TEXT, reply_markup=get_lead_main_keyboard())

    @router.message(F.text == Buttons.CANCEL)
    async def lead_cancel(message: Message, state: FSMContext):
        current_state = await state.get_state()
        if not current_state:
            return

        data = await state.get_data()
        return_to = data.get("return_to", "main")
        await state.clear()

        if return_to == "tasks":
            await message.answer(ACTION_CANCELLED_TEXT, reply_markup=get_lead_tasks_keyboard())
        elif return_to == "reports":
            await message.answer(ACTION_CANCELLED_TEXT, reply_markup=get_lead_reports_keyboard())
        else:
            await message.answer(ACTION_CANCELLED_TEXT, reply_markup=get_lead_main_keyboard())

    @router.message(F.text == Buttons.LEAD_TASKS_LIST)
    async def lead_tasks_list(message: Message, state: FSMContext):
        await state.clear()
        tasks = await asyncio.to_thread(tasks_service.list_tasks_created_by, message.from_user.id)

        if not tasks:
            await message.answer(
                LEAD_TASKS_EMPTY_TEXT,
                reply_markup=get_lead_tasks_keyboard(),
            )
            return

        await message.answer(
            LEAD_TASKS_LIST_TEXT,
            reply_markup=get_lead_tasks_keyboard(),
        )

        for task in tasks:
            assignee_label = await resolve_user_label(message.bot, task.employee_id)
            await message.answer(
                format_task_for_lead(task, assignee_label),
                parse_mode="HTML",
            )


    @router.message(F.text == Buttons.LEAD_TASK_PROPOSALS)
    async def lead_task_proposals_list(message: Message, state: FSMContext):
        await state.clear()
        requests = await asyncio.to_thread(
            task_request_service.list_requests_for_lead,
            message.from_user.id,
        )

        if not requests:
            await message.answer(
                LEAD_TASK_PROPOSALS_EMPTY_TEXT,
                reply_markup=get_lead_tasks_keyboard(),
            )
            return

        await message.answer(
            LEAD_TASK_PROPOSALS_LIST_TEXT,
            reply_markup=get_lead_tasks_keyboard(),
        )

        for request in requests:
            employee_label = await resolve_user_label(message.bot, request.author_id)
            await message.answer(
                format_task_proposal_for_lead(request, employee_label),
                reply_markup=get_task_proposal_action_keyboard(request.callback_token),
                parse_mode="HTML",
            )

    @router.callback_query(F.data.startswith(f"{TASK_PROPOSAL_CALLBACK_PREFIX}:"))
    async def lead_task_proposal_action(callback: CallbackQuery, state: FSMContext):
        _, action, token = callback.data.split(":", 2)

        request = await asyncio.to_thread(
            task_request_service.get_request_for_lead_by_token,
            token,
            callback.from_user.id,
        )
        if request is None:
            await callback.answer(LEAD_TASK_PROPOSAL_NOT_FOUND_TEXT, show_alert=True)
            return

        if action == "reject":
            await asyncio.to_thread(task_request_service.delete_request, request)
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer(
                LEAD_TASK_PROPOSAL_REJECT_SUCCESS,
                reply_markup=get_lead_tasks_keyboard(),
            )
            await callback.answer()
            return

        if action == "accept":
            await state.set_state(LeadStates.waiting_task_proposal_deadline)
            await state.update_data(
                task_proposal_token=request.callback_token,
                task_proposal_message_chat_id=callback.message.chat.id if callback.message else None,
                task_proposal_message_id=callback.message.message_id if callback.message else None,
                return_to="tasks",
            )
            await callback.message.answer(
                LEAD_TASK_PROPOSAL_ACCEPT_DEADLINE_PROMPT,
                reply_markup=calendar_for_today(),
            )
            await callback.answer()
            return

        await callback.answer(LEAD_TASK_PROPOSAL_NOT_FOUND_TEXT, show_alert=True)

    @router.callback_query(LeadStates.waiting_task_proposal_deadline, F.data.startswith(f"{CAL_PREFIX}:"))
    async def lead_task_proposal_deadline_calendar(call: CallbackQuery, state: FSMContext):
        parts = call.data.split(":")
        action = parts[1]

        if action == "ignore":
            await call.answer()
            return

        if action == "cancel":
            await state.clear()
            await call.message.edit_text(ACTION_CANCELLED_TEXT)
            await call.message.answer(LEAD_TASKS_TEXT, reply_markup=get_lead_tasks_keyboard())
            await call.answer()
            return

        if action == "nav":
            year = int(parts[2])
            month = int(parts[3])
            await call.message.edit_text(
                LEAD_TASK_PROPOSAL_ACCEPT_DEADLINE_PROMPT,
                reply_markup=build_calendar(year, month),
            )
            await call.answer()
            return

        if action != "pick":
            await call.answer()
            return

        year = int(parts[2])
        month = int(parts[3])
        day = int(parts[4])
        deadline = date(year, month, day).strftime("%Y-%m-%d")

        data = await state.get_data()
        token = data.get("task_proposal_token")
        request = await asyncio.to_thread(
            task_request_service.get_request_for_lead_by_token,
            token,
            call.from_user.id,
        )

        if request is None:
            await state.clear()
            await call.message.edit_text(LEAD_TASK_PROPOSAL_NOT_FOUND_TEXT)
            await call.message.answer(LEAD_TASKS_TEXT, reply_markup=get_lead_tasks_keyboard())
            await call.answer()
            return

        try:
            await asyncio.to_thread(
                tasks_service.create_task_created,
                request.title,
                request.description,
                request.author_id,
                call.from_user.id,
                deadline,
                request.created_at,
                None,
            )
            await asyncio.to_thread(task_request_service.delete_related_requests, request)
        except Exception as exc:
            logger.exception("Ошибка принятия предложенной задачи: %s", exc)
            await state.clear()
            await call.message.answer(
                f"Ошибка при принятии задачи: {exc}",
                reply_markup=get_lead_tasks_keyboard(),
            )
            await call.answer()
            return

        proposal_message_chat_id = data.get("task_proposal_message_chat_id")
        proposal_message_id = data.get("task_proposal_message_id")

        await state.clear()

        if proposal_message_chat_id and proposal_message_id:
            try:
                await call.bot.delete_message(
                    chat_id=proposal_message_chat_id,
                    message_id=proposal_message_id,
                )
            except Exception:
                pass

        await call.message.edit_text(LEAD_CREATE_TASK_DEADLINE_SELECTED.format(deadline=deadline))
        await call.message.answer(
            LEAD_TASK_PROPOSAL_ACCEPT_SUCCESS,
            reply_markup=get_lead_tasks_keyboard(),
        )
        await call.answer()

    @router.message(F.text == Buttons.LEAD_CREATE_TASK)
    async def lead_task_create_start(message: Message, state: FSMContext):
        await state.clear()
        await state.set_state(LeadStates.waiting_task_title)
        await message.answer(LEAD_CREATE_TASK_TITLE_PROMPT, reply_markup=get_lead_cancel_keyboard())

    @router.message(LeadStates.waiting_task_title, F.text)
    async def lead_task_title_input(message: Message, state: FSMContext):
        title = message.text.strip()
        if not title:
            await message.answer(LEAD_CREATE_TASK_TITLE_PROMPT, reply_markup=get_lead_cancel_keyboard())
            return

        await state.update_data(task_title=title)
        await state.set_state(LeadStates.waiting_task_description)
        await message.answer(LEAD_CREATE_TASK_DESCRIPTION_PROMPT, reply_markup=get_lead_cancel_keyboard())

    @router.message(LeadStates.waiting_task_description, F.text)
    async def lead_task_description_input(message: Message, state: FSMContext):
        description = message.text.strip()
        if description == "-":
            description = ""

        await state.update_data(task_description=description)
        await state.set_state(LeadStates.waiting_task_deadline)

        await message.answer(
            LEAD_CREATE_TASK_DEADLINE_PROMPT,
            reply_markup=calendar_for_today(),
        )

    @router.callback_query(LeadStates.waiting_task_deadline, F.data.startswith(f"{CAL_PREFIX}:"))
    async def lead_deadline_calendar(call: CallbackQuery, state: FSMContext):
        parts = call.data.split(":")
        action = parts[1]

        if action == "ignore":
            await call.answer()
            return

        if action == "cancel":
            await state.clear()
            await call.message.edit_text(ACTION_CANCELLED_TEXT)
            await call.message.answer(LEAD_TASKS_TEXT, reply_markup=get_lead_tasks_keyboard())
            await call.answer()
            return

        if action == "nav":
            year = int(parts[2])
            month = int(parts[3])
            await call.message.edit_text(
                LEAD_CREATE_TASK_DEADLINE_PROMPT,
                reply_markup=build_calendar(year, month),
            )
            await call.answer()
            return

        if action == "pick":
            year = int(parts[2])
            month = int(parts[3])
            day = int(parts[4])
            deadline = date(year, month, day).strftime("%Y-%m-%d")

            await state.update_data(deadline=deadline)
            await state.set_state(LeadStates.waiting_task_employee)

            await call.message.edit_text(LEAD_CREATE_TASK_DEADLINE_SELECTED.format(deadline=deadline))
            await call.answer()

            lead_id = call.from_user.id
            employee_ids = await asyncio.to_thread(auth_service.get_team_members_for_manager, lead_id)

            if not employee_ids:
                await state.clear()
                await call.message.answer(
                    LEAD_CREATE_TASK_NO_EMPLOYEES_TEXT,
                    reply_markup=get_lead_tasks_keyboard(),
                )
                return

            employee_options: dict[str, int] = {}
            employee_names: list[str] = []

            idx = 1
            for emp_id in employee_ids:
                display = None
                try:
                    chat = await call.bot.get_chat(emp_id)
                    if getattr(chat, "username", None):
                        display = f"@{chat.username}"
                    elif getattr(chat, "full_name", None):
                        display = chat.full_name
                except Exception as exc:
                    logger.warning("Не удалось получить данные исполнителя %s: %s", emp_id, exc)

                if not display:
                    display = f"Пользователь {idx}"
                    idx += 1

                base = display
                i = 2
                while display in employee_options:
                    display = f"{base} ({i})"
                    i += 1

                employee_options[display] = emp_id
                employee_names.append(display)

            await state.update_data(employee_options=employee_options)

            await call.message.answer(
                LEAD_CREATE_TASK_SELECT_EMPLOYEE_PROMPT,
                reply_markup=get_employee_selection_keyboard(employee_names),
            )

    @router.message(LeadStates.waiting_task_employee, F.text)
    async def lead_task_employee_select(message: Message, state: FSMContext):
        data = await state.get_data()
        employee_options: dict[str, int] = data.get("employee_options", {})
        selected = message.text.strip()

        if selected not in employee_options:
            await message.answer(
                LEAD_CREATE_TASK_INVALID_EMPLOYEE_TEXT,
                reply_markup=get_employee_selection_keyboard(list(employee_options.keys())),
            )
            return

        employee_id = employee_options[selected]
        title = data.get("task_title", "")
        description = data.get("task_description", "")
        deadline = data.get("deadline", "")
        author_id = message.from_user.id

        try:
            await asyncio.to_thread(
                tasks_service.create_task_created,
                title,
                description,
                employee_id,
                author_id,
                deadline,
            )
        except Exception as exc:
            logger.exception("Ошибка записи задачи в Google Sheets: %s", exc)
            await state.clear()
            await message.answer(
                f"Ошибка при создании задачи: {exc}",
                reply_markup=get_lead_tasks_keyboard(),
            )
            return

        await state.clear()
        await message.answer(LEAD_CREATE_TASK_SUCCESS, reply_markup=get_lead_tasks_keyboard())

    @router.message(F.text == Buttons.LEAD_REPORTS_LIST)
    async def lead_reports_list(message: Message, state: FSMContext):
        await state.clear()
        reports = await asyncio.to_thread(reports_service.get_all_reports)

        report_items: list[tuple[TaskRecord, ReportRecord]] = []
        for report in reports:
            task = await asyncio.to_thread(tasks_service.get_task_by_id, report.task_id)
            if task is None:
                continue
            if task.author_id != message.from_user.id:
                continue
            if (task.status or "").strip().lower() != "on consideration":
                continue
            report_items.append((task, report))

        if not report_items:
            await message.answer(
                LEAD_REPORTS_EMPTY_TEXT,
                reply_markup=get_lead_reports_keyboard(),
            )
            return

        await message.answer(
            LEAD_REPORTS_LIST_TEXT,
            reply_markup=get_lead_reports_keyboard(),
        )

        for task, report in report_items:
            employee_label = await resolve_user_label(message.bot, task.employee_id)
            await message.answer(
                format_report_summary_for_lead(task, employee_label),
                reply_markup=get_lead_report_item_keyboard(task.task_id),
                parse_mode="HTML",
            )

    @router.callback_query(F.data.startswith(f"{LEAD_REPORT_CALLBACK_PREFIX}:"))
    async def lead_report_action(callback: CallbackQuery, state: FSMContext):
        _, action, task_id = callback.data.split(":", 2)

        task = await asyncio.to_thread(tasks_service.get_task_by_id, task_id)
        if task is None:
            await callback.answer(TASK_NOT_FOUND_TEXT, show_alert=True)
            return

        if task.author_id != callback.from_user.id:
            await callback.answer(LEAD_REPORT_NOT_FOUND_TEXT, show_alert=True)
            return

        report = await asyncio.to_thread(reports_service.get_report_by_task_id, task_id)
        if report is None:
            await callback.answer(LEAD_REPORT_NOT_FOUND_TEXT, show_alert=True)
            return

        if action == "view":
            employee_label = await resolve_user_label(callback.bot, task.employee_id)
            await callback.message.answer(
                format_report_details_for_lead(task, employee_label, report),
                parse_mode="HTML",
            )
            await callback.answer()
            return

        if action == "accept":
            await state.update_data(
                task_id=task_id,
                accept_message_chat_id=callback.message.chat.id,
                accept_message_id=callback.message.message_id,
            )
            await callback.message.answer(
                LEAD_ACCEPT_REPORT_COMMENT_QUESTION,
                reply_markup=get_lead_accept_comment_choice_keyboard(task_id),
            )
            await callback.answer()
            return

        if action == "reject":
            await state.set_state(LeadStates.waiting_reject_comment)
            await state.update_data(
                task_id=task_id,
                return_to="reports",
                reject_message_chat_id=callback.message.chat.id,
                reject_message_id=callback.message.message_id,
            )
            await callback.message.answer(
                LEAD_REJECT_REPORT_PROMPT,
                reply_markup=get_lead_cancel_keyboard(),
            )
            await callback.answer()
            return

        await callback.answer(LEAD_REPORT_NOT_FOUND_TEXT, show_alert=True)

    @router.callback_query(F.data.startswith("lead_report_comment:no:"))
    async def lead_report_accept_without_comment(callback: CallbackQuery, state: FSMContext):
        task_id = callback.data.split(":")[-1]

        task = await asyncio.to_thread(tasks_service.get_task_by_id, task_id)
        if task is None:
            await callback.message.answer(TASK_NOT_FOUND_TEXT)
            await callback.answer()
            return

        report = await asyncio.to_thread(reports_service.get_report_by_task_id, task_id)
        if report is None:
            await callback.message.answer(LEAD_REPORT_NOT_FOUND_TEXT)
            await callback.answer()
            return

        await asyncio.to_thread(
            accepted_tasks_service.create_from_report,
            report,
            task,
            "",
        )
        await asyncio.to_thread(reports_service.delete_report_by_task_id, task_id)
        await asyncio.to_thread(tasks_service.delete_task_by_id, task_id)

        try:
            await callback.message.delete()
        except Exception:
            pass

        data = await state.get_data()
        accept_message_chat_id = data.get("accept_message_chat_id")
        accept_message_id = data.get("accept_message_id")

        if accept_message_chat_id and accept_message_id:
            try:
                await callback.bot.delete_message(
                    chat_id=accept_message_chat_id,
                    message_id=accept_message_id,
                )
            except Exception:
                pass

        await state.clear()
        await callback.message.answer(LEAD_ACCEPT_REPORT_SUCCESS)
        await callback.answer()

    @router.callback_query(F.data.startswith("lead_report_comment:yes:"))
    async def lead_report_accept_with_comment_start(callback: CallbackQuery, state: FSMContext):
        task_id = callback.data.split(":")[-1]

        data = await state.get_data()
        await state.set_state(LeadStates.waiting_accept_comment)
        await state.update_data(
            task_id=task_id,
            accept_message_chat_id=data.get("accept_message_chat_id"),
            accept_message_id=data.get("accept_message_id"),
        )

        try:
            await callback.message.delete()
        except Exception:
            pass

        await callback.message.answer(LEAD_ACCEPT_REPORT_COMMENT_PROMPT)
        await callback.answer()

    @router.message(LeadStates.waiting_accept_comment, F.text)
    async def lead_report_accept_with_comment_finish(message: Message, state: FSMContext):
        data = await state.get_data()
        task_id = data.get("task_id")
        comment = message.text.strip()
        accept_message_chat_id = data.get("accept_message_chat_id")
        accept_message_id = data.get("accept_message_id")

        if not comment:
            await message.answer(LEAD_REJECT_COMMENT_EMPTY)
            return

        task = await asyncio.to_thread(tasks_service.get_task_by_id, task_id)
        if task is None:
            await state.clear()
            await message.answer(TASK_NOT_FOUND_TEXT)
            return

        report = await asyncio.to_thread(reports_service.get_report_by_task_id, task_id)
        if report is None:
            await state.clear()
            await message.answer(LEAD_REPORT_NOT_FOUND_TEXT)
            return

        await asyncio.to_thread(
            accepted_tasks_service.create_from_report,
            report,
            task,
            comment,
        )
        await asyncio.to_thread(reports_service.delete_report_by_task_id, task_id)
        await asyncio.to_thread(tasks_service.delete_task_by_id, task_id)

        if accept_message_chat_id and accept_message_id:
            try:
                await message.bot.delete_message(
                    chat_id=accept_message_chat_id,
                    message_id=accept_message_id,
                )
            except Exception:
                pass

        await state.clear()
        await message.answer(LEAD_ACCEPT_REPORT_WITH_COMMENT_SUCCESS)

    @router.message(LeadStates.waiting_reject_comment, F.text)
    async def lead_report_reject_finish(message: Message, state: FSMContext):
        data = await state.get_data()
        task_id = data.get("task_id")
        comment = message.text.strip()
        reject_message_chat_id = data.get("reject_message_chat_id")
        reject_message_id = data.get("reject_message_id")

        if not comment:
            await message.answer(
                LEAD_REJECT_COMMENT_EMPTY,
                reply_markup=get_lead_cancel_keyboard(),
            )
            return

        task = await asyncio.to_thread(tasks_service.get_task_by_id, task_id)
        if task is None:
            await state.clear()
            await message.answer(TASK_NOT_FOUND_TEXT, reply_markup=get_lead_reports_keyboard())
            return

        report = await asyncio.to_thread(reports_service.get_report_by_task_id, task_id)
        if report is None:
            await state.clear()
            await message.answer(LEAD_REPORT_NOT_FOUND_TEXT, reply_markup=get_lead_reports_keyboard())
            return

        await asyncio.to_thread(
            reports_service.update_manager_feedback,
            task_id,
            comment,
        )

        await asyncio.to_thread(tasks_service.update_task_status, task_id, "cancelled")

        if reject_message_chat_id and reject_message_id:
            try:
                await message.bot.delete_message(
                    chat_id=reject_message_chat_id,
                    message_id=reject_message_id,
                )
            except Exception as exc:
                logger.warning(
                    "Не удалось удалить сообщение с отклоненным отчетом %s/%s: %s",
                    reject_message_chat_id,
                    reject_message_id,
                    exc,
                )

        try:
            await message.bot.send_message(
                task.employee_id,
                (
                    f"Отчет по задаче «{task.title}» отправлен на доработку.\n\n"
                    f"Комментарий руководителя:\n{comment}\n\n"
                    f"Задача снова доступна в списке задач."
                ),
            )
        except Exception as exc:
            logger.warning(
                "Не удалось отправить уведомление сотруднику %s: %s",
                task.employee_id,
                exc,
            )

        await state.clear()
        await message.answer(
            LEAD_REJECT_REPORT_SUCCESS,
            reply_markup=get_lead_reports_keyboard(),
        )

    @router.message(LeadStates.waiting_weekly_user, F.text)
    async def lead_weekly_input(message: Message, state: FSMContext):
        data = await state.get_data()
        employee_options = data.get("weekly_employee_options") or {}
        selected_label = (message.text or "").strip()
        employee_id = employee_options.get(selected_label)

        if employee_id is None:
            await message.answer(
                LEAD_WEEKLY_INVALID_EMPLOYEE_TEXT,
                reply_markup=get_employee_selection_keyboard(list(employee_options.keys()), include_exit=False),
            )
            return

        today = date.fromisoformat(await asyncio.to_thread(daily_reports_service.today_str))
        period_options = _build_week_period_options(today)

        await state.set_state(LeadStates.waiting_weekly_period)
        await state.update_data(
            return_to="reports",
            weekly_employee_id=employee_id,
            weekly_employee_label=selected_label,
            weekly_period_options=period_options,
        )
        await message.answer(
            LEAD_WEEKLY_PERIOD_TEXT,
            reply_markup=get_week_period_selection_keyboard(list(period_options.keys())),
        )

    @router.message(LeadStates.waiting_weekly_period, F.text)
    async def lead_weekly_period_input(message: Message, state: FSMContext):
        data = await state.get_data()
        period_options = data.get("weekly_period_options") or {}
        selected_period = (message.text or "").strip()
        period = period_options.get(selected_period)

        if period is None:
            await message.answer(
                LEAD_WEEKLY_INVALID_PERIOD_TEXT,
                reply_markup=get_week_period_selection_keyboard(list(period_options.keys())),
            )
            return

        employee_id = data.get("weekly_employee_id")
        if employee_id is None:
            await state.clear()
            await message.answer(LEAD_WEEKLY_INVALID_EMPLOYEE_TEXT, reply_markup=get_lead_reports_keyboard())
            return

        today = date.fromisoformat(await asyncio.to_thread(daily_reports_service.today_str))
        week_start = date.fromisoformat(period[0])
        week_end = date.fromisoformat(period[1])
        work_dates = _work_dates_between(week_start, min(week_end, today), _parse_days_of_week(default_days_of_week))

        stats = await asyncio.to_thread(
            _build_weekly_report_stats,
            accepted_tasks_service,
            tasks_service,
            visits_service,
            daily_reports_service,
            employee_id,
            week_start,
            week_end,
            work_dates,
            today,
        )

        employee_label = await resolve_user_label(message.bot, employee_id)
        closed_tasks = stats["closed_tasks"]
        assigned_tasks = stats["assigned_tasks"]
        overdue_tasks = stats["overdue_tasks"]

        await state.clear()
        await message.answer(
            LEAD_WEEKLY_RESULT_TEXT.format(
                employee_label=employee_label,
                week_start=week_start.isoformat(),
                week_end=week_end.isoformat(),
                closed_tasks_count=len(closed_tasks),
                closed_tasks_list=_format_task_items(closed_tasks, include_closed_date=True),
                assigned_tasks_count=len(assigned_tasks),
                assigned_tasks_list=_format_task_items(assigned_tasks, include_assignment_date=True),
                overdue_tasks_count=len(overdue_tasks),
                overdue_tasks_list=_format_task_items(overdue_tasks, include_deadline=True),
                worked_hours=_format_hours(stats["worked_hours"]),
                missing_daily_reports_count=stats["missing_daily_reports_count"],
            ),
            reply_markup=get_lead_reports_keyboard(),
            parse_mode="HTML",
        )

    return router