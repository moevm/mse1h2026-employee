import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants.bot_constants import Buttons
from constants.texts import (
    COMPLETE_TASK_TEXT,
    EMPLOYEE_TASKS_EMPTY_TEXT,
    EMPLOYEE_TASKS_LIST_TEXT,
    OFFER_TASK_TITLE_PROMPT,
    REPORT_COMMENT_TEXT,
    TASK_ACTION_NOT_ALLOWED_TEXT,
    TASK_ACCEPT_SUCCESS_TEXT,
    TASK_FINISH_SUCCESS_TEXT,
    TASK_NOT_FOUND_TEXT,
    TASK_STATUS_ALREADY_CHANGED_TEXT,
    VISIT_FINISH_NO_OPEN_TEXT,
    VISIT_FINISH_SUCCESS_TEXT,
    VISIT_START_ALREADY_OPEN_TEXT,
    VISIT_START_SUCCESS_TEXT,
)
from filters.active_role import ActiveRoleFilter
from services.tasks_service import format_task_for_assignee
from handlers.common import resolve_user_label
from keyboards.role_menus import (
    TASK_CALLBACK_PREFIX,
    get_employee_menu_keyboard,
    get_manager_selection_keyboard,
    get_task_action_keyboard,
)
from roles import Role
from services.auth_service import AuthService
from services.tasks_service import TasksService
from services.visits_service import VisitsService
from states.task_request import TaskRequestStates


def setup_employee_router(
    auth_service: AuthService,
    visits_service: VisitsService,
    tasks_service: TasksService,
):
    router = Router()
    router.message.filter(ActiveRoleFilter(auth_service, Role.EMPLOYEE))
    router.callback_query.filter(ActiveRoleFilter(auth_service, Role.EMPLOYEE))

    @router.message(F.text == Buttons.START_WORK)
    async def start_work(message: Message):
        success = visits_service.start_workday(message.from_user.id)

        if success:
            await message.answer(
                VISIT_START_SUCCESS_TEXT,
                reply_markup=get_employee_menu_keyboard(),
            )
        else:
            await message.answer(
                VISIT_START_ALREADY_OPEN_TEXT,
                reply_markup=get_employee_menu_keyboard(),
            )

    @router.message(F.text == Buttons.FINISH_WORK)
    async def finish_work(message: Message):
        success = visits_service.finish_workday(message.from_user.id)

        if success:
            await message.answer(
                VISIT_FINISH_SUCCESS_TEXT,
                reply_markup=get_employee_menu_keyboard(),
            )
        else:
            await message.answer(
                VISIT_FINISH_NO_OPEN_TEXT,
                reply_markup=get_employee_menu_keyboard(),
            )

    @router.message(F.text == Buttons.EMPLOYEE_CREATE_TASK)
    async def create_my_task(message: Message, state: FSMContext):
        await state.clear()
        await state.set_state(TaskRequestStates.waiting_title)
        await message.answer(
            OFFER_TASK_TITLE_PROMPT,
            reply_markup=get_manager_selection_keyboard([]),
        )

    @router.message(F.text == Buttons.EMPLOYEE_TASKS_LIST)
    async def my_task_list(message: Message):
        tasks = await asyncio.to_thread(tasks_service.list_tasks_assigned_to, message.from_user.id)

        if not tasks:
            await message.answer(
                EMPLOYEE_TASKS_EMPTY_TEXT,
                reply_markup=get_employee_menu_keyboard(),
            )
            return

        await message.answer(
            EMPLOYEE_TASKS_LIST_TEXT,
            reply_markup=get_employee_menu_keyboard(),
        )

        for task in tasks:
            author_label = await resolve_user_label(message.bot, task.author_id)
            await message.answer(
                format_task_for_assignee(task, author_label),
                reply_markup=get_task_action_keyboard(task.task_id, task.status),
                parse_mode="HTML",
            )

    @router.callback_query(F.data.startswith(f"{TASK_CALLBACK_PREFIX}:"))
    async def process_task_action(callback: CallbackQuery):
        _, action, task_id = callback.data.split(":", 2)
        task = await asyncio.to_thread(tasks_service.get_task_by_id, task_id)

        if task is None:
            await callback.answer(TASK_NOT_FOUND_TEXT, show_alert=True)
            return

        if task.employee_id != callback.from_user.id:
            await callback.answer(TASK_ACTION_NOT_ALLOWED_TEXT, show_alert=True)
            return

        if action == "accept":
            if task.status != "created":
                await callback.answer(TASK_STATUS_ALREADY_CHANGED_TEXT, show_alert=True)
                return
            updated_task = await asyncio.to_thread(tasks_service.update_task_status, task_id, "in process")
            success_text = TASK_ACCEPT_SUCCESS_TEXT
        elif action == "finish":
            if task.status != "in process":
                await callback.answer(TASK_STATUS_ALREADY_CHANGED_TEXT, show_alert=True)
                return
            updated_task = await asyncio.to_thread(tasks_service.update_task_status, task_id, "finished")
            success_text = TASK_FINISH_SUCCESS_TEXT
        else:
            await callback.answer(TASK_ACTION_NOT_ALLOWED_TEXT, show_alert=True)
            return

        if updated_task is None:
            await callback.answer(TASK_NOT_FOUND_TEXT, show_alert=True)
            return

        author_label = await resolve_user_label(callback.bot, updated_task.author_id)
        await callback.message.edit_text(
            format_task_for_assignee(updated_task, author_label),
            reply_markup=get_task_action_keyboard(updated_task.task_id, updated_task.status),
            parse_mode="HTML",
        )
        await callback.answer(success_text)

    @router.message(F.text == Buttons.EMPLOYEE_COMPLETE_TASK)
    async def complete_task(message: Message):
        await message.answer(COMPLETE_TASK_TEXT, reply_markup=get_employee_menu_keyboard())

    @router.message(F.text == Buttons.EMPLOYEE_REPORT_COMMENT)
    async def report_comment(message: Message):
        await message.answer(REPORT_COMMENT_TEXT, reply_markup=get_employee_menu_keyboard())

    return router