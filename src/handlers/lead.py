import asyncio
import logging
from datetime import date
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
    LEAD_REPORT_NOT_FOUND_TEXT,
    LEAD_REPORTS_EMPTY_TEXT,
    LEAD_REPORTS_LIST_TEXT,
    LEAD_REPORTS_TEXT,
    LEAD_TASKS_EMPTY_TEXT,
    LEAD_TASKS_LIST_TEXT,
    LEAD_TASKS_TEXT,
    LEAD_VIEW_REPORT_SUCCESS,
    LEAD_WEEKLY_SUCCESS,
    LEAD_WEEKLY_TEXT,
    TASK_NOT_FOUND_TEXT,
    VISIT_FINISH_NO_OPEN_TEXT,
    VISIT_FINISH_SUCCESS_TEXT,
    VISIT_START_ALREADY_OPEN_TEXT,
    VISIT_START_SUCCESS_TEXT,
    LEAD_REJECT_REPORT_PROMPT,
    LEAD_REJECT_REPORT_SUCCESS,
    LEAD_REJECT_COMMENT_EMPTY,
)
from filters.active_role import ActiveRoleFilter
from handlers.common import resolve_user_label
from keyboards.inline_calendar import CAL_PREFIX, build_calendar, calendar_for_today
from keyboards.role_menus import (
    LEAD_REPORT_CALLBACK_PREFIX,
    get_employee_selection_keyboard,
    get_lead_accept_comment_choice_keyboard,
    get_lead_cancel_keyboard,
    get_lead_main_keyboard,
    get_lead_report_item_keyboard,
    get_lead_reports_keyboard,
    get_lead_tasks_keyboard,
)
from roles import Role
from services.accepted_tasks_service import AcceptedTasksService
from services.auth_service import AuthService
from services.reports_service import ReportRecord, ReportsService
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


def setup_lead_router(
    auth_service: AuthService,
    tasks_service: TasksService,
    visits_service: VisitsService,
    reports_service: ReportsService,
    accepted_tasks_service: AcceptedTasksService,
):
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

    @router.message(F.text == Buttons.LEAD_TASKS)
    async def lead_tasks_menu(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(LEAD_TASKS_TEXT, reply_markup=get_lead_tasks_keyboard())

    @router.message(F.text == Buttons.LEAD_REPORTS)
    async def lead_reports_menu(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(LEAD_REPORTS_TEXT, reply_markup=get_lead_reports_keyboard())

    @router.message(F.text == Buttons.LEAD_WEEKLY_REPORT)
    async def lead_weekly_start(message: Message, state: FSMContext):
        await state.set_state(LeadStates.waiting_weekly_user)
        await state.update_data(return_to="main")
        await message.answer(LEAD_WEEKLY_TEXT, reply_markup=get_lead_cancel_keyboard())

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
                "Нужен комментарий к принятому отчету?",
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
            await callback.message.answer("Задача не найдена.")
            await callback.answer()
            return

        report = await asyncio.to_thread(reports_service.get_report_by_task_id, task_id)
        if report is None:
            await callback.message.answer("Отчет не найден.")
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
        await callback.message.answer("Отчет принят.")
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

        await callback.message.answer("Введите комментарий к отчету одним сообщением.")
        await callback.answer()

    @router.message(LeadStates.waiting_accept_comment, F.text)
    async def lead_report_accept_with_comment_finish(message: Message, state: FSMContext):
        data = await state.get_data()
        task_id = data.get("task_id")
        comment = message.text.strip()
        accept_message_chat_id = data.get("accept_message_chat_id")
        accept_message_id = data.get("accept_message_id")

        if not comment:
            await message.answer("Комментарий пустой. Введите комментарий еще раз.")
            return

        task = await asyncio.to_thread(tasks_service.get_task_by_id, task_id)
        if task is None:
            await state.clear()
            await message.answer("Задача не найдена.")
            return

        report = await asyncio.to_thread(reports_service.get_report_by_task_id, task_id)
        if report is None:
            await state.clear()
            await message.answer("Отчет не найден.")
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
        await message.answer("Отчет принят с комментарием.")

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
            await message.answer("Задача не найдена.", reply_markup=get_lead_reports_keyboard())
            return

        report = await asyncio.to_thread(reports_service.get_report_by_task_id, task_id)
        if report is None:
            await state.clear()
            await message.answer("Отчет не найден.", reply_markup=get_lead_reports_keyboard())
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
        await state.clear()
        await message.answer(LEAD_WEEKLY_SUCCESS, reply_markup=get_lead_main_keyboard())

    return router