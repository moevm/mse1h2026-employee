import asyncio
import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants.bot_constants import Buttons
from constants.texts import (
    ACTION_CANCELLED_TEXT,
    OFFER_TASK_TITLE_PROMPT,
    OFFER_TASK_DESCRIPTION_PROMPT,
    OFFER_TASK_INVALID_MANAGER_TEXT,
    OFFER_TASK_MANAGER_PROMPT,
    OFFER_TASK_NO_MANAGERS_TEXT,
    OFFER_TASK_SUCCESS_TEXT,
)
from filters.active_role import ActiveRoleFilter
from keyboards.role_menus import (
    get_employee_menu_keyboard,
    get_manager_selection_keyboard,
)
from roles import Role
from services.auth_service import AuthService
from services.task_request_service import TaskRequestService
from states.task_request import TaskRequestStates

logger = logging.getLogger(__name__)


def setup_task_request_router(
    auth_service: AuthService,
    task_request_service: TaskRequestService,
):
    router = Router()
    router.message.filter(ActiveRoleFilter(auth_service, Role.EMPLOYEE))

    @router.message(TaskRequestStates.waiting_title, F.text == Buttons.CANCEL)
    @router.message(TaskRequestStates.waiting_description, F.text == Buttons.CANCEL)
    @router.message(TaskRequestStates.waiting_manager, F.text == Buttons.CANCEL)
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
            reply_markup=get_manager_selection_keyboard([]),
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

        manager_options: dict[str, int] = {}
        manager_names: list[str] = []

        for manager_id in manager_ids:
            display_name = f"ID:{manager_id}"
            try:
                chat = await message.bot.get_chat(manager_id)
                if chat.username:
                    display_name = f"@{chat.username}"
            except Exception as exc:
                logger.warning(
                    "Не удалось получить username руководителя %s: %s",
                    manager_id,
                    exc,
                )

            manager_options[display_name] = manager_id
            manager_names.append(display_name)

        await state.update_data(
            description=description,
            manager_options=manager_options,
        )
        await state.set_state(TaskRequestStates.waiting_manager)
        await message.answer(
            f"Руководители: {', '.join(manager_names)}",
            reply_markup=get_manager_selection_keyboard(manager_names),
        )
        await message.answer(OFFER_TASK_MANAGER_PROMPT)

    @router.message(TaskRequestStates.waiting_manager, F.text)
    async def offer_task_manager(message: Message, state: FSMContext):
        data = await state.get_data()
        manager_options = data.get("manager_options", {})
        selected_manager = message.text.strip()

        if selected_manager not in manager_options:
            await message.answer(
                OFFER_TASK_INVALID_MANAGER_TEXT,
                reply_markup=get_manager_selection_keyboard(list(manager_options.keys())),
            )
            return

        title = data.get("title", "")
        description = data.get("description", "")
        lead_id = manager_options[selected_manager]
        author_id = message.from_user.id

        await asyncio.to_thread(
            task_request_service.create_request,
            title,
            description,
            lead_id,
            author_id,
        )

        await state.clear()
        await message.answer(
            OFFER_TASK_SUCCESS_TEXT,
            reply_markup=get_employee_menu_keyboard(),
        )

    return router
