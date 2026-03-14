from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message, TelegramObject

from roles import Role
from services.auth_service import AuthService


class ActiveRoleFilter(BaseFilter):
    def __init__(self, auth_service: AuthService, *roles: Role):
        self.auth_service = auth_service
        self.roles = set(roles)

    async def __call__(self, event: TelegramObject) -> bool:
        user = None

        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        else:
            user = getattr(event, "from_user", None)

        if user is None:
            return False

        active_role = self.auth_service.get_active_role(user.id)
        return active_role in self.roles
