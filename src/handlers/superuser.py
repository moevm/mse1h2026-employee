import asyncio
import logging

from aiogram.fsm.context import FSMContext
from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery

from constants.bot_constants import Buttons
from constants.texts import (
    BAN_USER_NOT_READY_TEXT,
    SUPERUSER_REVOKE_ROLE_EMPTY_TEXT,
    SUPERUSER_REVOKE_ROLE_LAST_SUPERUSER,
    SUPERUSER_REVOKE_ROLE_LIST_TEXT,
    SUPERUSER_REVOKE_ROLE_NOT_FOUND,
    SUPERUSER_REVOKE_ROLE_SUCCESS,
    SUPERUSER_ROLE_REQUESTS_EMPTY_TEXT,
)
from filters.active_role import ActiveRoleFilter
from keyboards.role_menus import (
    SUPERUSER_REVOKE_CALLBACK_PREFIX,
    get_superuser_menu_keyboard,
    get_role_request_action_keyboard,
    get_superuser_revoke_role_keyboard,
)
from roles import Role
from services.auth_service import AuthService, AuthUser
from services.role_request_service import RoleRequestService

logger = logging.getLogger(__name__)


def _build_user_display(chat, tg_id: int) -> str:
    if getattr(chat, "username", None):
        return f"@{chat.username}"
    if getattr(chat, "first_name", None):
        return f"<a href='tg://user?id={tg_id}'>{chat.first_name}</a>"
    return f"<a href='tg://user?id={tg_id}'>Пользователь {tg_id}</a>"


def _superuser_count(auth_service: AuthService) -> int:
    return sum(1 for user in auth_service.get_all_users() if Role.SUPERUSER in user.roles)


async def _resolve_user_display(bot: Bot, tg_id: int) -> str:
    try:
        chat = await bot.get_chat(tg_id)
        return _build_user_display(chat, tg_id)
    except Exception as exc:
        logger.warning("Ошибка при получении данных пользователя %s: %s", tg_id, exc)
        return f"<a href='tg://user?id={tg_id}'>Пользователь {tg_id}</a>"


def setup_superuser_router(
    auth_service: AuthService, role_request_service: RoleRequestService
):
    router = Router()
    router.message.filter(ActiveRoleFilter(auth_service, Role.SUPERUSER))
    router.callback_query.filter(ActiveRoleFilter(auth_service, Role.SUPERUSER))

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

    @router.message(F.text == Buttons.SUPERUSER_REVOKE_ROLE)
    async def revoke_role_list_handler(message: Message, state: FSMContext, bot: Bot):
        users = await asyncio.to_thread(auth_service.get_all_users)

        if not users:
            await message.answer(
                SUPERUSER_REVOKE_ROLE_EMPTY_TEXT,
                reply_markup=get_superuser_menu_keyboard(),
            )
            return

        await state.clear()
        revoke_message_ids: list[int] = []

        header = await message.answer(
            SUPERUSER_REVOKE_ROLE_LIST_TEXT,
            reply_markup=get_superuser_menu_keyboard(),
        )
        revoke_message_ids.append(header.message_id)

        for user in users:
            display = await _resolve_user_display(bot, user.tg_id)
            roles_text = ", ".join(role.title for role in user.roles)

            sent = await message.answer(
                f"<b>Пользователь:</b> {display}\n"
                f"<b>Роли:</b> {roles_text}",
                reply_markup=get_superuser_revoke_role_keyboard(
                    user.tg_id,
                    [role.value for role in user.roles],
                ),
                parse_mode="HTML",
            )
            revoke_message_ids.append(sent.message_id)

        await state.update_data(revoke_role_message_ids=revoke_message_ids)
    
    @router.callback_query(F.data.startswith(f"{SUPERUSER_REVOKE_CALLBACK_PREFIX}:"))
    async def revoke_role_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
        _, tg_id_str, role_value = callback.data.split(":", 2)
        tg_id = int(tg_id_str)

        try:
            role = Role(role_value)
        except ValueError:
            await callback.answer("Неизвестная роль.", show_alert=True)
            return

        if role == Role.SUPERUSER:
            superuser_count = await asyncio.to_thread(_superuser_count, auth_service)
            if superuser_count <= 1 and auth_service.can_login_as_role(tg_id, Role.SUPERUSER):
                await callback.answer(SUPERUSER_REVOKE_ROLE_LAST_SUPERUSER, show_alert=True)
                return

        success = await asyncio.to_thread(auth_service.revoke_role, tg_id, role)
        if not success:
            await callback.answer(SUPERUSER_REVOKE_ROLE_NOT_FOUND, show_alert=True)
            return

        user_roles = await asyncio.to_thread(auth_service.get_user_roles, tg_id)
        display = await _resolve_user_display(bot, tg_id)

        if user_roles:
            roles_text = ", ".join(item.title for item in user_roles)
            await callback.message.edit_text(
                f"<b>Пользователь:</b> {display}\n"
                f"<b>Роли:</b> {roles_text}",
                reply_markup=get_superuser_revoke_role_keyboard(
                    tg_id,
                    [item.value for item in user_roles],
                ),
                parse_mode="HTML",
            )
        else:
            await callback.message.edit_text(
                f"<b>Пользователь:</b> {display}\n"
                f"<b>Роли:</b> нет ролей",
                parse_mode="HTML",
            )

        data = await state.get_data()
        revoke_message_ids: list[int] = data.get("revoke_role_message_ids", [])
        current_message_id = callback.message.message_id
        chat_id = callback.message.chat.id

        for message_id in revoke_message_ids:
            if message_id == current_message_id:
                continue
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id)
            except Exception:
                pass

        await state.update_data(revoke_role_message_ids=[current_message_id])

        await callback.answer(SUPERUSER_REVOKE_ROLE_SUCCESS.format(role=role.title))

    @router.message(F.text == Buttons.SUPERUSER_BAN_USER)
    async def ban_user_handler(message: Message):
        await message.answer(
            BAN_USER_NOT_READY_TEXT,
            reply_markup=get_superuser_menu_keyboard(),
        )

    return router
