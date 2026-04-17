import asyncio
from html import escape

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from constants.bot_constants import Buttons
from constants.texts import (
    COMPLETE_TASK_TEXT,
    INTERN_TASKS_EMPTY_TEXT,
    INTERN_TASKS_LIST_TEXT,
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
    REPORT_TEXT_PROMPT,
    REPORT_EMPTY_TEXT,
    REPORT_SENT_TEXT,
    ACTION_CANCELLED_TEXT,
)
from filters.active_role import ActiveRoleFilter
from services.tasks_service import format_task_for_assignee
from handlers.common import resolve_user_label
from keyboards.role_menus import (
    TASK_CALLBACK_PREFIX,
    get_intern_menu_keyboard,
    get_task_action_keyboard,
    get_report_cancel_keyboard,
)
from roles import Role
from services.auth_service import AuthService
from services.tasks_service import TasksService
from services.visits_service import VisitsService
from services.reports_service import ReportsService
from states.task_report import TaskReportStates


def setup_intern_router(
    auth_service: AuthService,
    visits_service: VisitsService,
    tasks_service: TasksService,
    reports_service: ReportsService,
):
    router = Router()
    router.message.filter(ActiveRoleFilter(auth_service, Role.INTERN))
    router.callback_query.filter(ActiveRoleFilter(auth_service, Role.INTERN))

    @router.message(F.text == Buttons.START_WORK)
    async def start_work(message: Message):
        success = visits_service.start_workday(message.from_user.id)

        if success:
            await message.answer(
                VISIT_START_SUCCESS_TEXT,
                reply_markup=get_intern_menu_keyboard(),
            )
        else:
            await message.answer(
                VISIT_START_ALREADY_OPEN_TEXT,
                reply_markup=get_intern_menu_keyboard(),
            )

    @router.message(F.text == Buttons.FINISH_WORK)
    async def finish_work(message: Message):
        success = visits_service.finish_workday(message.from_user.id)

        if success:
            await message.answer(
                VISIT_FINISH_SUCCESS_TEXT,
                reply_markup=get_intern_menu_keyboard(),
            )
        else:
            await message.answer(
                VISIT_FINISH_NO_OPEN_TEXT,
                reply_markup=get_intern_menu_keyboard(),
            )

    @router.message(F.text == Buttons.INTERN_TASKS_LIST)
    async def my_task_list(message: Message):
        tasks = await asyncio.to_thread(tasks_service.list_tasks_assigned_to, message.from_user.id)
        tasks = [
            t for t in tasks
            if (t.status or "").strip().lower() in ("created", "in process", "finished", "cancelled")
        ]

        if not tasks:
            await message.answer(
                INTERN_TASKS_EMPTY_TEXT,
                reply_markup=get_intern_menu_keyboard(),
            )
            return

        await message.answer(
            INTERN_TASKS_LIST_TEXT,
            reply_markup=get_intern_menu_keyboard(),
        )

        for task in tasks:
            author_label = await resolve_user_label(message.bot, task.author_id)
            task_text = format_task_for_assignee(task, author_label)

            if (task.status or "").strip().lower() == "cancelled":
                manager_feedback = await asyncio.to_thread(
                    reports_service.get_manager_feedback_by_task_id,
                    task.task_id,
                )
                if manager_feedback:
                    task_text += f"\n\n<b>Комментарий руководителя:</b>\n{escape(manager_feedback)}"

            await message.answer(
                task_text,
                reply_markup=get_task_action_keyboard(task.task_id, task.status),
                parse_mode="HTML",
            )

    @router.callback_query(F.data.startswith(f"{TASK_CALLBACK_PREFIX}:"))
    async def process_task_action(callback: CallbackQuery, state: FSMContext):
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
        elif action == "report":
            if (task.status or "").strip().lower() not in ("in process", "on consideration", "finished", "cancelled"):
                await callback.answer(TASK_ACTION_NOT_ALLOWED_TEXT, show_alert=True)
                return

            await state.clear()
            await state.set_state(TaskReportStates.waiting_report_text)
            await state.update_data(
                report_task_id=task_id,
                report_msg_chat_id=callback.message.chat.id,
                report_msg_id=callback.message.message_id,
            )

            await callback.message.answer(REPORT_TEXT_PROMPT, reply_markup=get_report_cancel_keyboard())
            await callback.answer()
            return
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

    @router.message(F.text == Buttons.INTERN_COMPLETE_TASK)
    async def complete_task(message: Message):
        await message.answer(COMPLETE_TASK_TEXT, reply_markup=get_intern_menu_keyboard())

    @router.message(F.text == Buttons.INTERN_REPORT_COMMENT)
    async def report_comment(message: Message):
        await message.answer(REPORT_COMMENT_TEXT, reply_markup=get_intern_menu_keyboard())

    @router.message(TaskReportStates.waiting_report_text, F.text == Buttons.CANCEL)
    async def report_cancel(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(ACTION_CANCELLED_TEXT, reply_markup=get_intern_menu_keyboard())


    @router.message(TaskReportStates.waiting_report_text, F.text)
    async def report_send(message: Message, state: FSMContext):
        report_text = message.text.strip()
        if not report_text:
            await message.answer(REPORT_EMPTY_TEXT, reply_markup=get_report_cancel_keyboard())
            return

        data = await state.get_data()
        task_id = data.get("report_task_id")
        msg_chat_id = data.get("report_msg_chat_id")
        msg_id = data.get("report_msg_id")

        if not task_id:
            await state.clear()
            await message.answer(TASK_NOT_FOUND_TEXT, reply_markup=get_intern_menu_keyboard())
            return

        task = await asyncio.to_thread(tasks_service.get_task_by_id, task_id)
        if task is None:
            await state.clear()
            await message.answer(TASK_NOT_FOUND_TEXT, reply_markup=get_intern_menu_keyboard())
            return

        if task.employee_id != message.from_user.id:
            await state.clear()
            await message.answer(TASK_ACTION_NOT_ALLOWED_TEXT, reply_markup=get_intern_menu_keyboard())
            return

        await asyncio.to_thread(tasks_service.update_task_status, task_id, "on consideration")
        updated_task = await asyncio.to_thread(tasks_service.get_task_by_id, task_id)

        await asyncio.to_thread(
            reports_service.create_report,
            task_id,
            message.from_user.id,
            report_text,
        )

        if updated_task and msg_chat_id and msg_id:
            author_label = await resolve_user_label(message.bot, updated_task.author_id)
            try:
                await message.bot.edit_message_text(
                    chat_id=msg_chat_id,
                    message_id=msg_id,
                    text=format_task_for_assignee(updated_task, author_label),
                    reply_markup=get_task_action_keyboard(updated_task.task_id, updated_task.status),
                    parse_mode="HTML",
                )
            except Exception:
                pass

        await state.clear()
        await message.answer(REPORT_SENT_TEXT, reply_markup=get_intern_menu_keyboard())

    return router
