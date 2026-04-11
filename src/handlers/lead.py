import asyncio
import logging
from datetime import date

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants.bot_constants import Buttons
from constants.texts import (
    ACTION_CANCELLED_TEXT,
    LEAD_CONFIRM_REPORT_SUCCESS,
    LEAD_CREATE_TASK_DEADLINE_PROMPT,
    LEAD_CREATE_TASK_DEADLINE_SELECTED,
    LEAD_CREATE_TASK_DESCRIPTION_PROMPT,
    LEAD_CREATE_TASK_INVALID_EMPLOYEE_TEXT,
    LEAD_CREATE_TASK_NO_EMPLOYEES_TEXT,
    LEAD_CREATE_TASK_SELECT_EMPLOYEE_PROMPT,
    LEAD_CREATE_TASK_SUCCESS,
    LEAD_CREATE_TASK_TITLE_PROMPT,
    LEAD_DENY_REPORT_PROMPT,
    LEAD_DENY_REPORT_SUCCESS,
    LEAD_MENU_TEXT,
    LEAD_OPEN_REPORT_PROMPT,
    LEAD_OPEN_REPORT_SUCCESS,
    LEAD_REPORTS_LIST_TEXT,
    LEAD_REPORTS_TEXT,
    LEAD_TASKS_EMPTY_TEXT,
    LEAD_TASKS_LIST_TEXT,
    LEAD_TASKS_TEXT,
    LEAD_WEEKLY_SUCCESS,
    LEAD_WEEKLY_TEXT,
    VISIT_FINISH_NO_OPEN_TEXT,
    VISIT_FINISH_SUCCESS_TEXT,
    VISIT_START_ALREADY_OPEN_TEXT,
    VISIT_START_SUCCESS_TEXT,
)
from filters.active_role import ActiveRoleFilter
from services.tasks_service import format_task_for_lead
from handlers.common import resolve_user_label
from keyboards.inline_calendar import CAL_PREFIX, build_calendar, calendar_for_today
from keyboards.role_menus import (
    get_employee_selection_keyboard,
    get_lead_cancel_keyboard,
    get_lead_main_keyboard,
    get_lead_report_actions_keyboard,
    get_lead_reports_keyboard,
    get_lead_tasks_keyboard,
)
from roles import Role
from services.auth_service import AuthService
from services.tasks_service import TasksService
from services.visits_service import VisitsService
from states.lead import LeadStates

logger = logging.getLogger(__name__)


def setup_lead_router(
    auth_service: AuthService,
    tasks_service: TasksService,
    visits_service: VisitsService,
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
        await message.answer(LEAD_REPORTS_LIST_TEXT, reply_markup=get_lead_reports_keyboard())

    @router.message(F.text == Buttons.LEAD_OPEN_REPORT)
    async def lead_report_open_start(message: Message, state: FSMContext):
        await state.set_state(LeadStates.waiting_report_id)
        await state.update_data(return_to="reports")
        await message.answer(LEAD_OPEN_REPORT_PROMPT, reply_markup=get_lead_cancel_keyboard())

    @router.message(LeadStates.waiting_report_id, F.text)
    async def lead_report_open_input(message: Message, state: FSMContext):
        report_id = message.text.strip().strip("'").strip('"')
        await state.set_state(LeadStates.viewing_report)
        await state.update_data(current_report_id=report_id)
        await message.answer(
            LEAD_OPEN_REPORT_SUCCESS.format(report_id=report_id),
            reply_markup=get_lead_report_actions_keyboard(),
        )

    @router.message(LeadStates.viewing_report, F.text == Buttons.LEAD_CONFIRM_REPORT)
    async def lead_report_confirm(message: Message, state: FSMContext):
        data = await state.get_data()
        report_id = data.get("current_report_id", "UNKNOWN")
        await state.clear()
        await message.answer(
            LEAD_CONFIRM_REPORT_SUCCESS.format(report_id=report_id),
            reply_markup=get_lead_reports_keyboard(),
        )

    @router.message(LeadStates.viewing_report, F.text == Buttons.LEAD_DENY_REPORT)
    async def lead_report_deny_start(message: Message, state: FSMContext):
        data = await state.get_data()
        report_id = data.get("current_report_id", "UNKNOWN")
        await state.set_state(LeadStates.waiting_deny_comment)
        await state.update_data(return_to="reports", current_report_id=report_id)
        await message.answer(
            LEAD_DENY_REPORT_PROMPT.format(report_id=report_id),
            reply_markup=get_lead_cancel_keyboard(),
        )

    @router.message(LeadStates.waiting_deny_comment, F.text)
    async def lead_report_deny_comment(message: Message, state: FSMContext):
        data = await state.get_data()
        report_id = data.get("current_report_id", "UNKNOWN")
        comment = message.text.strip()
        await state.clear()
        await message.answer(
            LEAD_DENY_REPORT_SUCCESS.format(report_id=report_id, comment=comment),
            reply_markup=get_lead_reports_keyboard(),
        )

    @router.message(LeadStates.viewing_report, F.text == Buttons.LEAD_BACK_TO_REPORTS)
    async def lead_back_to_reports(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(LEAD_REPORTS_TEXT, reply_markup=get_lead_reports_keyboard())

    @router.message(LeadStates.waiting_weekly_user, F.text)
    async def lead_weekly_input(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(LEAD_WEEKLY_SUCCESS, reply_markup=get_lead_main_keyboard())

    return router
