from aiogram import F, Router
from aiogram.types import Message

from constants.bot_constants import Buttons
from constants.texts import (
    COMPLETE_TASK_TEXT,
    MY_TASKS_TEXT, 
    REPORT_COMMENT_TEXT,
    VISIT_START_SUCCESS_TEXT,
    VISIT_START_ALREADY_OPEN_TEXT,
    VISIT_FINISH_SUCCESS_TEXT,
    VISIT_FINISH_NO_OPEN_TEXT
)
from filters.active_role import ActiveRoleFilter
from keyboards.role_menus import get_intern_menu_keyboard
from roles import Role
from services.auth_service import AuthService
from services.visits_service import VisitsService


def setup_intern_router(auth_service: AuthService, visits_service: VisitsService):
    router = Router()
    router.message.filter(ActiveRoleFilter(auth_service, Role.INTERN))

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
        await message.answer(MY_TASKS_TEXT, reply_markup=get_intern_menu_keyboard())

    @router.message(F.text == Buttons.INTERN_COMPLETE_TASK)
    async def complete_task(message: Message):
        await message.answer(COMPLETE_TASK_TEXT, reply_markup=get_intern_menu_keyboard())

    @router.message(F.text == Buttons.INTERN_REPORT_COMMENT)
    async def report_comment(message: Message):
        await message.answer(REPORT_COMMENT_TEXT, reply_markup=get_intern_menu_keyboard())

    return router
