from aiogram import F, Router, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove
import re
from datetime import time
from html import escape
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from constants.bot_constants import Buttons
from constants.texts import (
    ACTION_CANCELLED_TEXT,
    EMPLOYEE_MENU_TEXT,
    INTERN_MENU_TEXT,
    LEAD_MENU_TEXT,
    LOGOUT_TEXT,
    NOTIFICATION_SETTINGS_FORMAT_ERROR_TEXT,
    NOTIFICATION_SETTINGS_ORDER_ERROR_TEXT,
    NOTIFICATION_SETTINGS_SUCCESS_TEXT,
    NOTIFICATION_SETTINGS_TEXT,
    NOTIFICATION_SETTINGS_TIME_ERROR_TEXT,
    NOTIFICATION_SETTINGS_TIMEZONE_ERROR_TEXT,
    SUPERUSER_MENU_TEXT,
    WELCOME_TEXT,
    EXIT_WITH_OPEN_VISIT_TEXT,
)
from keyboards.auth_menu import get_start_menu_keyboard
from keyboards.role_menus import (
    get_employee_menu_keyboard,
    get_intern_menu_keyboard,
    get_lead_main_keyboard,
    get_superuser_menu_keyboard,
    get_cancel_keyboard,
)
from roles import Role
from services.auth_service import AuthService
from services.visits_service import VisitsService
from states.notification_settings import NotificationSettingsStates


async def resolve_user_label(bot: Bot, user_id: int | None) -> str:
    if user_id is None:
        return "Не указан"

    try:
        chat = await bot.get_chat(user_id)
    except Exception:
        return f"ID: {user_id}"

    if getattr(chat, "username", None):
        return f"@{escape(chat.username)}"
    if getattr(chat, "full_name", None):
        return escape(chat.full_name)
    if getattr(chat, "first_name", None):
        return escape(chat.first_name)

    return f"ID: {user_id}"


def get_role_menu(role: Role):
    if role == Role.SUPERUSER:
        return SUPERUSER_MENU_TEXT, get_superuser_menu_keyboard()
    if role == Role.LEAD:
        return LEAD_MENU_TEXT, get_lead_main_keyboard()
    if role == Role.EMPLOYEE:
        return EMPLOYEE_MENU_TEXT, get_employee_menu_keyboard()
    if role == Role.INTERN:
        return INTERN_MENU_TEXT, get_intern_menu_keyboard()

    raise ValueError(f"Неподдерживаемая роль: {role}")


def _parse_notification_settings(raw_text: str) -> tuple[str, str, str] | None:
    parts = raw_text.split()

    if len(parts) != 3:
        return None

    return parts[0], parts[1], parts[2]


def _parse_user_time(value: str) -> time | None:
    value = str(value).strip()

    match = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", value)

    if not match:
        return None

    hours = int(match.group(1))
    minutes = int(match.group(2))
    seconds = int(match.group(3) or 0)

    if hours > 23 or minutes > 59 or seconds > 59:
        return None

    return time(hour=hours, minute=minutes)


def _normalize_time(value: str) -> str:
    parsed_time = _parse_user_time(value)

    if parsed_time is None:
        raise ValueError("Invalid time")

    return parsed_time.strftime("%H:%M")


def setup_common_router(
    auth_service: AuthService,
    visits_service: VisitsService,
    default_morning_time: str = "08:50",
    default_evening_time: str = "16:50",
    default_timezone: str = "Europe/Moscow",
):
    router = Router()

    @router.message(F.text == Buttons.NOTIFICATION_SETTINGS)
    async def notification_settings_start(message: Message, state: FSMContext):
        tg_id = message.from_user.id
        active_role = auth_service.get_active_role(tg_id)

        if active_role is None:
            await message.answer(
                WELCOME_TEXT,
                reply_markup=get_start_menu_keyboard(),
            )
            return

        settings = auth_service.get_notification_settings(
            tg_id,
            default_morning_time,
            default_evening_time,
            default_timezone,
        )

        await state.set_state(NotificationSettingsStates.waiting_settings)

        await message.answer(
            NOTIFICATION_SETTINGS_TEXT.format(**settings),
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard(),
        )

    @router.message(NotificationSettingsStates.waiting_settings, F.text == Buttons.CANCEL)
    async def notification_settings_cancel(message: Message, state: FSMContext):
        await state.clear()

        active_role = auth_service.get_active_role(message.from_user.id)

        if active_role is None:
            await message.answer(
                ACTION_CANCELLED_TEXT,
                reply_markup=get_start_menu_keyboard(),
            )
            return

        _, keyboard = get_role_menu(active_role)

        await message.answer(
            ACTION_CANCELLED_TEXT,
            reply_markup=keyboard,
        )

    @router.message(NotificationSettingsStates.waiting_settings, F.text)
    async def notification_settings_save(message: Message, state: FSMContext):
        parsed = _parse_notification_settings(message.text.strip())

        if parsed is None:
            await message.answer(
                NOTIFICATION_SETTINGS_FORMAT_ERROR_TEXT,
                parse_mode="HTML",
            )
            return

        morning_time, evening_time, timezone = parsed

        parsed_morning_time = _parse_user_time(morning_time)
        parsed_evening_time = _parse_user_time(evening_time)

        if parsed_morning_time is None or parsed_evening_time is None:
            await message.answer(NOTIFICATION_SETTINGS_TIME_ERROR_TEXT)
            return

        if parsed_morning_time >= parsed_evening_time:
            await message.answer(NOTIFICATION_SETTINGS_ORDER_ERROR_TEXT)
            return

        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError:
            await message.answer(NOTIFICATION_SETTINGS_TIMEZONE_ERROR_TEXT)
            return

        morning_time = parsed_morning_time.strftime("%H:%M")
        evening_time = parsed_evening_time.strftime("%H:%M")

        auth_service.set_notification_settings(
            message.from_user.id,
            morning_time,
            evening_time,
            timezone,
        )

        await state.clear()

        active_role = auth_service.get_active_role(message.from_user.id)
        _, keyboard = (
            get_role_menu(active_role)
            if active_role
            else (None, get_start_menu_keyboard())
        )

        await message.answer(
            NOTIFICATION_SETTINGS_SUCCESS_TEXT.format(
                morning_time=morning_time,
                evening_time=evening_time,
                timezone=timezone,
            ),
            reply_markup=keyboard,
        )

    @router.message(F.text == Buttons.EXIT)
    async def exit_handler(message: Message):
        tg_id = message.from_user.id
        active_role = auth_service.get_active_role(tg_id)

        if active_role in {Role.LEAD, Role.EMPLOYEE, Role.INTERN}:
            if visits_service.has_open_visit(tg_id):
                await message.answer(EXIT_WITH_OPEN_VISIT_TEXT)
                return

        auth_service.logout(tg_id)

        await message.answer(
            LOGOUT_TEXT,
            reply_markup=ReplyKeyboardRemove(),
        )

        await message.answer(
            WELCOME_TEXT,
            reply_markup=get_start_menu_keyboard(),
        )

    return router