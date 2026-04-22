import asyncio

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants.bot_constants import Buttons
from constants.texts import (
    ACTION_CANCELLED_TEXT,
    OFFER_TASK_TITLE_PROMPT,
    OFFER_TASK_DESCRIPTION_PROMPT,
    OFFER_TASK_NO_MANAGERS_TEXT,
    OFFER_TASK_SUCCESS_TEXT,
)
from filters.active_role import ActiveRoleFilter
from keyboards.role_menus import (
    get_cancel_keyboard,
    get_employee_menu_keyboard,
)
from roles import Role
from services.auth_service import AuthService
from services.task_request_service import TaskRequestService
from states.task_request import TaskRequestStates


def setup_task_request_router(
    auth_service: AuthService,
    task_request_service: TaskRequestService,
):
    router = Router()
    router.message.filter(ActiveRoleFilter(auth_service, Role.EMPLOYEE))

    @router.message(TaskRequestStates.waiting_title, F.text == Buttons.CANCEL)
    @router.message(TaskRequestStates.waiting_description, F.text == Buttons.CANCEL)
    async def offer_task_cancel(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(
            ACTION_CANCELLED_TEXT,
            reply_markup=get_employee_menu_keyboard(),
        )

    @router.message(TaskRequestStates.waiting_title, F.text)
    async def offer_task_title(message: Message, state: FSMContext):
        title = message.text.strip()
        if not title:
            await message.answer(OFFER_TASK_TITLE_PROMPT)
            return

        await state.update_data(title=title)
        await state.set_state(TaskRequestStates.waiting_description)
        await message.answer(
            OFFER_TASK_DESCRIPTION_PROMPT,
            reply_markup=get_cancel_keyboard(),
        )

    @router.message(TaskRequestStates.waiting_description, F.text)
    async def offer_task_description(message: Message, state: FSMContext):
        description = message.text.strip()
        if not description:
            await message.answer(OFFER_TASK_DESCRIPTION_PROMPT)
            return

        manager_ids = await asyncio.to_thread(
            auth_service.get_manager_ids_for_user,
            message.from_user.id,
            Role.EMPLOYEE,
        )

        if not manager_ids:
            await state.clear()
            await message.answer(
                OFFER_TASK_NO_MANAGERS_TEXT,
                reply_markup=get_employee_menu_keyboard(),
            )
            return

        data = await state.get_data()
        title = data.get("title", "")
        author_id = message.from_user.id

        await asyncio.to_thread(
            task_request_service.create_requests,
            title,
            description,
            manager_ids,
            author_id,
        )

        await state.clear()
        await message.answer(
            OFFER_TASK_SUCCESS_TEXT,
            reply_markup=get_employee_menu_keyboard(),
        )

    return router
