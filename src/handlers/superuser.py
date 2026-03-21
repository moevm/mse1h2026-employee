import asyncio
import logging

from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery

from constants.bot_constants import Buttons
from constants.texts import (
    BAN_USER_NOT_READY_TEXT,
    LEAD_MENU_TEXT,
    SUPERUSER_ROLE_REQUESTS_EMPTY_TEXT,
)
from filters.active_role import ActiveRoleFilter
from keyboards.role_menus import (
    get_lead_main_keyboard,
    get_superuser_menu_keyboard,
    get_role_request_action_keyboard,
)
from roles import Role
from services.auth_service import AuthService
from services.role_request_service import RoleRequestService

logger = logging.getLogger(__name__)


def setup_superuser_router(
    auth_service: AuthService, role_request_service: RoleRequestService
):
    router = Router()
    router.message.filter(ActiveRoleFilter(auth_service, Role.SUPERUSER))

    @router.message(F.text == Buttons.SUPERUSER_ROLE_REQUESTS)
    async def role_requests_handler(message: Message, bot: Bot):
        requests = await asyncio.to_thread(role_request_service.get_all_requests)

        if not requests:
            await message.answer(
                SUPERUSER_ROLE_REQUESTS_EMPTY_TEXT,
                reply_markup=get_superuser_menu_keyboard(),
            )
            return

        await message.answer(
            "<b>Список активных запросов на роли:</b>", parse_mode="HTML"
        )

        for req in requests:
            tg_id_str = str(req.get("Telegram ID", "")).strip()
            role_val = str(req.get("Role", "")).strip()

            if not tg_id_str:
                continue

            username_display = (
                f"<a href='tg://user?id={tg_id_str}'>Пользователь {tg_id_str}</a>"
            )

            try:
                chat = await bot.get_chat(int(tg_id_str))
                if chat.username:
                    username_display = f"@{chat.username}"
                elif chat.first_name:
                    username_display = (
                        f"<a href='tg://user?id={tg_id_str}'>{chat.first_name}</a>"
                    )
            except Exception as e:
                logger.warning(f"Ошибка при получении данных: {e}")

            text = (
                f"Пользователь: {username_display}\nЗапрошенная роль: <b>{role_val}</b>"
            )

            await message.answer(
                text,
                reply_markup=get_role_request_action_keyboard(tg_id_str, role_val),
                parse_mode="HTML",
            )

    @router.callback_query(F.data.startswith("req_approve:"))
    async def approve_request_callback(callback: CallbackQuery):
        _, tg_id_str, role_str = callback.data.split(":")
        tg_id = int(tg_id_str)
        role = Role.from_str(role_str)

        if not role:
            await callback.answer("Ошибка: неверная роль.", show_alert=True)
            return

        await callback.answer("Выдаю роль...", show_alert=False)

        success = await asyncio.to_thread(
            role_request_service.approve_request, tg_id, role, auth_service
        )

        if success:
            await callback.message.edit_text(
                f"{callback.message.html_text}\n\n<b>Статус: Роль успешно выдана</b>",
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                f"{callback.message.html_text}\n\n<b>Статус: Ошибка. Запрос не найден</b>",
                parse_mode="HTML",
            )

    @router.callback_query(F.data.startswith("req_deny:"))
    async def deny_request_callback(callback: CallbackQuery):
        _, tg_id_str, role_str = callback.data.split(":")
        tg_id = int(tg_id_str)
        role = Role.from_str(role_str)

        if not role:
            await callback.answer("Ошибка: неверная роль.", show_alert=True)
            return

        await callback.answer("Отклоняю запрос...", show_alert=False)

        success = await asyncio.to_thread(
            role_request_service.deny_request, tg_id, role
        )

        if success:
            await callback.message.edit_text(
                f"{callback.message.html_text}\n\n<b>Статус: Запрос отклонен</b>",
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                f"{callback.message.html_text}\n\n<b>Статус: Ошибка. Запрос не найден</b>",
                parse_mode="HTML",
            )

    @router.message(F.text == Buttons.SUPERUSER_BAN_USER)
    async def ban_user_handler(message: Message):
        await message.answer(
            BAN_USER_NOT_READY_TEXT,
            reply_markup=get_superuser_menu_keyboard(),
        )

    @router.message(F.text == Buttons.SUPERUSER_LEAD_MENU)
    async def open_lead_menu_handler(message: Message):
        await message.answer(
            LEAD_MENU_TEXT,
            reply_markup=get_lead_main_keyboard(),
        )

    return router
