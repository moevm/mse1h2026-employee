import asyncio

from aiogram import F, Router
from aiogram.types import Message

from keyboards.auth_menu import (
    get_roles_keyboard,
    get_start_menu_keyboard,
    get_role_request_keyboard,
)
from roles import Role
from services.auth_service import AuthService
from constants.bot_constants import Buttons
from services.role_request_service import RoleRequestService
from constants.texts import (
    CHOOSE_ROLE_TEXT,
    NO_ACCESS_ROLE_TEXT,
    ROLE_REQUEST_CHOOSE_TEXT,
    ROLE_REQUEST_SENT_TEXT,
    NO_ROLES_TEXT,
    ROLE_SELECTED_TEXT,
    UNKNOWN_ROLE_TEXT,
    WELCOME_TEXT,
)
from handlers.common import get_role_menu


def setup_auth_router(
    auth_service: AuthService, role_request_service: RoleRequestService
):
    router = Router()

    @router.message(F.text == Buttons.AUTH)
    async def start_auth_handler(message: Message):
        tg_id = message.from_user.id
        user = auth_service.get_user(tg_id)

        if user is None:
            await message.answer(
                NO_ROLES_TEXT,
                reply_markup=get_start_menu_keyboard(),
            )
            return

        await message.answer(
            CHOOSE_ROLE_TEXT,
            reply_markup=get_roles_keyboard(user.roles),
        )

    @router.message(F.text.in_([role.title.capitalize() for role in Role]))
    async def choose_role_handler(message: Message):
        tg_id = message.from_user.id
        role = next(
            (current_role for current_role in Role if current_role.title.capitalize() == message.text),
            None,
        )

        if role is None:
            await message.answer(UNKNOWN_ROLE_TEXT)
            return

        if not auth_service.can_login_as_role(tg_id, role):
            await message.answer(NO_ACCESS_ROLE_TEXT)
            return

        auth_service.set_active_role(tg_id, role)
        menu_text, keyboard = get_role_menu(role)

        await message.answer(
            ROLE_SELECTED_TEXT.format(role=role.title),
        )
        await message.answer(menu_text, reply_markup=keyboard)

    @router.message(F.text == Buttons.BACK)
    async def back_to_start_handler(message: Message):
        await message.answer(
            WELCOME_TEXT,
            reply_markup=get_start_menu_keyboard(),
        )

    @router.message(F.text == Buttons.REQUEST_ROLE)
    async def request_role_handler(message: Message):
        await message.answer(
            ROLE_REQUEST_CHOOSE_TEXT,
            reply_markup=get_role_request_keyboard(),
        )

    @router.message(F.text.in_([Buttons.REQUEST_INTERN, Buttons.REQUEST_EMPLOYEE, Buttons.REQUEST_LEAD, Buttons.REQUEST_SUPERUSER,]))
    async def request_role_select_handler(message: Message):
        tg_id = message.from_user.id

        role = {
            Buttons.REQUEST_INTERN: Role.INTERN,
            Buttons.REQUEST_EMPLOYEE: Role.EMPLOYEE,
            Buttons.REQUEST_LEAD: Role.LEAD,
            Buttons.REQUEST_SUPERUSER: Role.SUPERUSER,
        }.get(message.text)

        if role is None:
            await message.answer(UNKNOWN_ROLE_TEXT)
            return

        if auth_service.can_login_as_role(tg_id, role):
            await message.answer("У вас уже есть эта роль")
            return
        
        await asyncio.to_thread(role_request_service.create_request, tg_id, role)

        await message.answer(
            ROLE_REQUEST_SENT_TEXT.format(role=role.value),
        )
        await message.answer(
            WELCOME_TEXT,
            reply_markup=get_start_menu_keyboard(),
        )

    return router