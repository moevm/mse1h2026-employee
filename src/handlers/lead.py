from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants.bot_constants import Buttons
from constants.texts import (
    ACTION_CANCELLED_TEXT,
    EMPLOYEE_MENU_TEXT,
    LEAD_CONFIRM_REPORT_SUCCESS,
    LEAD_CREATE_TASK_PROMPT,
    LEAD_CREATE_TASK_SUCCESS,
    LEAD_DENY_REPORT_PROMPT,
    LEAD_DENY_REPORT_SUCCESS,
    LEAD_MENU_TEXT,
    LEAD_OPEN_REPORT_PROMPT,
    LEAD_OPEN_REPORT_SUCCESS,
    LEAD_REPORTS_LIST_TEXT,
    LEAD_REPORTS_TEXT,
    LEAD_TASKS_LIST_TEXT,
    LEAD_TASKS_TEXT,
    LEAD_WEEKLY_SUCCESS,
    LEAD_WEEKLY_TEXT,
)
from filters.active_role import ActiveRoleFilter
from keyboards.role_menus import (
    get_employee_menu_keyboard,
    get_lead_cancel_keyboard,
    get_lead_main_keyboard,
    get_lead_report_actions_keyboard,
    get_lead_reports_keyboard,
    get_lead_tasks_keyboard,
)
from roles import Role
from services.auth_service import AuthService
from states.lead import LeadStates


def setup_lead_router(auth_service: AuthService):
    router = Router()
    router.message.filter(ActiveRoleFilter(auth_service, Role.LEAD, Role.SUPERUSER))

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

    @router.message(F.text == Buttons.LEAD_EMPLOYEE_MENU)
    async def lead_to_employee_menu(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(
            EMPLOYEE_MENU_TEXT,
            reply_markup=get_employee_menu_keyboard(),
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
        await message.answer(LEAD_TASKS_LIST_TEXT, reply_markup=get_lead_tasks_keyboard())

    @router.message(F.text == Buttons.LEAD_CREATE_TASK)
    async def lead_task_create_start(message: Message, state: FSMContext):
        await state.set_state(LeadStates.waiting_task_input)
        await state.update_data(return_to="tasks")
        await message.answer(LEAD_CREATE_TASK_PROMPT, reply_markup=get_lead_cancel_keyboard())

    @router.message(LeadStates.waiting_task_input, F.text)
    async def lead_task_create_input(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(LEAD_CREATE_TASK_SUCCESS, reply_markup=get_lead_main_keyboard())

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
