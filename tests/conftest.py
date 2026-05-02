from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class _FNode:
    def __getattr__(self, _name: str) -> "_FNode":
        return self

    def __eq__(self, other: object) -> tuple[str, object]:
        return ("eq", other)

    def in_(self, values: object) -> tuple[str, object]:
        return ("in", values)

    def startswith(self, value: str) -> tuple[str, str]:
        return ("startswith", value)


class _HandlerRegistry:
    def __init__(self, router: "Router", kind: str):
        self.router = router
        self.kind = kind
        self.filters: list[tuple[tuple[Any, ...], dict[str, Any]]] = []

    def filter(self, *args: Any, **kwargs: Any) -> None:
        self.filters.append((args, kwargs))

    def __call__(self, *filters: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            self.router.handlers.append(
                {
                    "kind": self.kind,
                    "name": func.__name__,
                    "filters": filters,
                    "kwargs": kwargs,
                    "func": func,
                }
            )
            return func

        return decorator


class Router:
    def __init__(self):
        self.handlers: list[dict[str, Any]] = []
        self.message = _HandlerRegistry(self, "message")
        self.callback_query = _HandlerRegistry(self, "callback_query")


class BaseFilter:
    async def __call__(self, event: object) -> bool:
        return True


class Bot:
    pass


class TelegramObject:
    pass


@dataclass
class User:
    id: int


@dataclass
class Chat:
    id: int = 1


class ReplyKeyboardRemove:
    pass


class InlineKeyboardButton:
    def __init__(self, text: str, callback_data: str | None = None):
        self.text = text
        self.callback_data = callback_data


class InlineKeyboardMarkup:
    def __init__(self, inline_keyboard: list[list[InlineKeyboardButton]] | None = None, **kwargs: Any):
        self.inline_keyboard = inline_keyboard or []
        self.kwargs = kwargs


class _KeyboardMarkup:
    def __init__(self, buttons: list[dict[str, Any]], *, resize_keyboard: bool | None = None):
        self.buttons = buttons
        self.resize_keyboard = resize_keyboard

    def texts(self) -> list[str]:
        return [button["text"] for button in self.buttons]


class ReplyKeyboardBuilder:
    def __init__(self):
        self.buttons: list[dict[str, Any]] = []
        self.adjust_sizes: tuple[int, ...] = ()

    def button(self, *, text: str) -> None:
        self.buttons.append({"text": text})

    def adjust(self, *sizes: int) -> None:
        self.adjust_sizes = sizes

    def as_markup(self, **kwargs: Any) -> _KeyboardMarkup:
        return _KeyboardMarkup(self.buttons, resize_keyboard=kwargs.get("resize_keyboard"))


class InlineKeyboardBuilder:
    def __init__(self):
        self.rows: list[list[InlineKeyboardButton]] = []
        self.current_buttons: list[InlineKeyboardButton] = []
        self.adjust_sizes: tuple[int, ...] = ()

    def button(self, *, text: str, callback_data: str) -> None:
        self.current_buttons.append(InlineKeyboardButton(text=text, callback_data=callback_data))

    def row(self, *buttons: InlineKeyboardButton) -> None:
        self.rows.append(list(buttons))

    def adjust(self, *sizes: int) -> None:
        self.adjust_sizes = sizes

    def as_markup(self, **_kwargs: Any) -> InlineKeyboardMarkup:
        rows = [*self.rows]
        if self.current_buttons:
            rows.append(self.current_buttons)
        return InlineKeyboardMarkup(rows)


class State:
    pass


class StatesGroup:
    pass


class FSMContext:
    pass


class Message(TelegramObject):
    pass


class CallbackQuery(TelegramObject):
    pass


aiogram = types.ModuleType("aiogram")
aiogram.F = _FNode()
aiogram.Router = Router
aiogram.Bot = Bot
sys.modules.setdefault("aiogram", aiogram)

aiogram_filters = types.ModuleType("aiogram.filters")
aiogram_filters.BaseFilter = BaseFilter
sys.modules.setdefault("aiogram.filters", aiogram_filters)

aiogram_types = types.ModuleType("aiogram.types")
aiogram_types.CallbackQuery = CallbackQuery
aiogram_types.Message = Message
aiogram_types.TelegramObject = TelegramObject
aiogram_types.InlineKeyboardMarkup = InlineKeyboardMarkup
aiogram_types.InlineKeyboardButton = InlineKeyboardButton
aiogram_types.ReplyKeyboardRemove = ReplyKeyboardRemove
sys.modules.setdefault("aiogram.types", aiogram_types)

aiogram_utils = types.ModuleType("aiogram.utils")
aiogram_utils_keyboard = types.ModuleType("aiogram.utils.keyboard")
aiogram_utils_keyboard.ReplyKeyboardBuilder = ReplyKeyboardBuilder
aiogram_utils_keyboard.InlineKeyboardBuilder = InlineKeyboardBuilder
sys.modules.setdefault("aiogram.utils", aiogram_utils)
sys.modules.setdefault("aiogram.utils.keyboard", aiogram_utils_keyboard)

aiogram_fsm = types.ModuleType("aiogram.fsm")
aiogram_fsm_context = types.ModuleType("aiogram.fsm.context")
aiogram_fsm_context.FSMContext = FSMContext
aiogram_fsm_state = types.ModuleType("aiogram.fsm.state")
aiogram_fsm_state.State = State
aiogram_fsm_state.StatesGroup = StatesGroup
sys.modules.setdefault("aiogram.fsm", aiogram_fsm)
sys.modules.setdefault("aiogram.fsm.context", aiogram_fsm_context)
sys.modules.setdefault("aiogram.fsm.state", aiogram_fsm_state)

gspread = types.ModuleType("gspread")
gspread.authorize = lambda credentials: None
sys.modules.setdefault("gspread", gspread)

google = types.ModuleType("google")
google_oauth2 = types.ModuleType("google.oauth2")
google_service_account = types.ModuleType("google.oauth2.service_account")

class Credentials:
    @staticmethod
    def from_service_account_file(*_args: Any, **_kwargs: Any) -> object:
        return object()

google_service_account.Credentials = Credentials
sys.modules.setdefault("google", google)
sys.modules.setdefault("google.oauth2", google_oauth2)
sys.modules.setdefault("google.oauth2.service_account", google_service_account)


class FakeBot:
    def __init__(self, chats: dict[int, object] | None = None):
        self.chats = chats or {}
        self.edited_messages: list[dict[str, Any]] = []

    async def get_chat(self, user_id: int) -> object:
        if user_id not in self.chats:
            raise LookupError(user_id)
        return self.chats[user_id]

    async def edit_message_text(self, **kwargs: Any) -> None:
        self.edited_messages.append(kwargs)


class FakeChatInfo:
    def __init__(self, username: str | None = None, full_name: str | None = None, first_name: str | None = None):
        self.username = username
        self.full_name = full_name
        self.first_name = first_name


class FakeMessage:
    def __init__(self, *, text: str = "", user_id: int = 100, bot: FakeBot | None = None, chat_id: int = 500, message_id: int = 10):
        self.text = text
        self.from_user = User(user_id)
        self.bot = bot or FakeBot()
        self.chat = Chat(chat_id)
        self.message_id = message_id
        self.answers: list[dict[str, Any]] = []
        self.edits: list[dict[str, Any]] = []

    async def answer(self, text: str, **kwargs: Any) -> None:
        self.answers.append({"text": text, **kwargs})

    async def edit_text(self, text: str, **kwargs: Any) -> None:
        self.edits.append({"text": text, **kwargs})


class FakeCallback:
    def __init__(self, *, data: str, user_id: int = 100, bot: FakeBot | None = None, message: FakeMessage | None = None):
        self.data = data
        self.from_user = User(user_id)
        self.bot = bot or FakeBot()
        self.message = message or FakeMessage(user_id=user_id, bot=self.bot)
        self.answers: list[dict[str, Any]] = []

    async def answer(self, text: str | None = None, **kwargs: Any) -> None:
        self.answers.append({"text": text, **kwargs})


class FakeState:
    def __init__(self, data: dict[str, Any] | None = None):
        self.data = data or {}
        self.state: object | None = None
        self.clear_count = 0
        self.set_states: list[object] = []
        self.update_calls: list[dict[str, Any]] = []

    async def clear(self) -> None:
        self.clear_count += 1
        self.data.clear()
        self.state = None

    async def set_state(self, state: object) -> None:
        self.state = state
        self.set_states.append(state)

    async def update_data(self, **kwargs: Any) -> None:
        self.data.update(kwargs)
        self.update_calls.append(kwargs)

    async def get_data(self) -> dict[str, Any]:
        return dict(self.data)


def get_handler(router: Router, name: str, *, kind: str | None = None) -> Callable[..., Any]:
    matches = [h for h in router.handlers if h["name"] == name and (kind is None or h["kind"] == kind)]
    assert matches, f"Handler {name!r} not found. Registered: {[h['name'] for h in router.handlers]}"
    return matches[0]["func"]
