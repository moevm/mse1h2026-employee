from __future__ import annotations

import asyncio
from types import SimpleNamespace

from conftest import FakeBot, FakeChatInfo, FakeCallback, FakeMessage, FakeState, get_handler
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
from handlers.superuser import setup_superuser_router
from keyboards.role_menus import SUPERUSER_REVOKE_CALLBACK_PREFIX
from roles import Role

from helpers import FakeAuthUser, FakeRoleRequestService, FakeSuperuserAuthService

def run(coro):
    return asyncio.run(coro)

def patch_answer_return_message_id(message: FakeMessage, *, start_id: int = 1000):
    orig_answer = message.answer
    counter = {"id": start_id}

    async def answer_with_msgid(text: str, **kwargs):
        await orig_answer(text, **kwargs)
        counter["id"] += 1
        return SimpleNamespace(message_id=counter["id"])

    message.answer = answer_with_msgid


def build_router(*, auth=None, req=None):
    return setup_superuser_router(
        auth_service=auth or FakeSuperuserAuthService(),
        role_request_service=req or FakeRoleRequestService(),
    )

def test_superuser_role_requests_empty():
    router = build_router(req=FakeRoleRequestService(requests=[]))
    bot = FakeBot()
    message = FakeMessage(user_id=900, bot=bot)

    run(get_handler(router, "role_requests_handler")(message, bot))

    assert message.answers[0]["text"] == SUPERUSER_ROLE_REQUESTS_EMPTY_TEXT
    assert Buttons.SUPERUSER_ROLE_REQUESTS in message.answers[0]["reply_markup"].texts()

def test_superuser_role_requests_list_renders_cards_and_actions():
    req = FakeRoleRequestService(
        requests=[
            {"Telegram ID": "111", "Role": "employee"},
            {"Telegram ID": "222", "Role": "lead"},
        ]
    )
    bot = FakeBot(
        chats={
            111: FakeChatInfo(username="alice"),
            222: FakeChatInfo(first_name="Bob"),
        }
    )
    router = build_router(req=req)
    message = FakeMessage(user_id=900, bot=bot)

    run(get_handler(router, "role_requests_handler")(message, bot))

    assert "Список активных запросов" in message.answers[0]["text"]

    assert "@alice" in message.answers[1]["text"]
    assert "employee" in message.answers[1]["text"]
    kb1 = message.answers[1]["reply_markup"].inline_keyboard
    assert kb1[0][0].callback_data.startswith("req_approve:111:employee")
    assert kb1[0][1].callback_data.startswith("req_deny:111:employee")

    assert "Bob" in message.answers[2]["text"]
    assert "lead" in message.answers[2]["text"]
    kb2 = message.answers[2]["reply_markup"].inline_keyboard
    assert kb2[0][0].callback_data.startswith("req_approve:222:lead")
    assert kb2[0][1].callback_data.startswith("req_deny:222:lead")

def test_superuser_role_requests_skips_rows_without_tg_id():
    req = FakeRoleRequestService(
        requests=[
            {"Telegram ID": "", "Role": "employee"},
            {"Telegram ID": "111", "Role": "employee"},
        ]
    )
    bot = FakeBot(chats={111: FakeChatInfo(username="alice")})
    router = build_router(req=req)
    message = FakeMessage(user_id=900, bot=bot)

    run(get_handler(router, "role_requests_handler")(message, bot))

    assert len(message.answers) == 2
    assert "@alice" in message.answers[1]["text"]

def test_superuser_approve_invalid_role_alert():
    router = build_router(req=FakeRoleRequestService())
    msg = FakeMessage(user_id=900)
    msg.html_text = "карточка"
    cb = FakeCallback(data="req_approve:111:not_a_role", user_id=900, message=msg)

    run(get_handler(router, "approve_request_callback", kind="callback_query")(cb))

    assert cb.answers[-1]["show_alert"] is True
    assert "неверная роль" in (cb.answers[-1]["text"] or "").lower()

def test_superuser_approve_success_edits_message():
    req = FakeRoleRequestService(approve_map={(111, "employee"): True})
    auth = FakeSuperuserAuthService()
    router = build_router(auth=auth, req=req)

    msg = FakeMessage(user_id=900)
    msg.html_text = "карточка"
    cb = FakeCallback(data="req_approve:111:employee", user_id=900, message=msg)

    run(get_handler(router, "approve_request_callback", kind="callback_query")(cb))

    assert req.approve_calls == [(111, Role.EMPLOYEE)]
    assert "Статус: Роль успешно выдана" in msg.edits[-1]["text"]

def test_superuser_approve_not_found_edits_message():
    req = FakeRoleRequestService(approve_map={(111, "employee"): False})
    router = build_router(req=req)

    msg = FakeMessage(user_id=900)
    msg.html_text = "карточка"
    cb = FakeCallback(data="req_approve:111:employee", user_id=900, message=msg)

    run(get_handler(router, "approve_request_callback", kind="callback_query")(cb))

    assert "Статус: Ошибка. Запрос не найден" in msg.edits[-1]["text"]

def test_superuser_deny_invalid_role_alert():
    router = build_router(req=FakeRoleRequestService())
    msg = FakeMessage(user_id=900)
    msg.html_text = "карточка"
    cb = FakeCallback(data="req_deny:111:not_a_role", user_id=900, message=msg)

    run(get_handler(router, "deny_request_callback", kind="callback_query")(cb))

    assert cb.answers[-1]["show_alert"] is True
    assert "неверная роль" in (cb.answers[-1]["text"] or "").lower()

def test_superuser_deny_success_edits_message():
    req = FakeRoleRequestService(deny_map={(111, "employee"): True})
    router = build_router(req=req)

    msg = FakeMessage(user_id=900)
    msg.html_text = "карточка"
    cb = FakeCallback(data="req_deny:111:employee", user_id=900, message=msg)

    run(get_handler(router, "deny_request_callback", kind="callback_query")(cb))

    assert req.deny_calls == [(111, Role.EMPLOYEE)]
    assert "Статус: Запрос отклонен" in msg.edits[-1]["text"]

def test_superuser_deny_not_found_edits_message():
    req = FakeRoleRequestService(deny_map={(111, "employee"): False})
    router = build_router(req=req)

    msg = FakeMessage(user_id=900)
    msg.html_text = "карточка"
    cb = FakeCallback(data="req_deny:111:employee", user_id=900, message=msg)

    run(get_handler(router, "deny_request_callback", kind="callback_query")(cb))

    assert "Статус: Ошибка. Запрос не найден" in msg.edits[-1]["text"]

def test_superuser_revoke_role_list_empty():
    auth = FakeSuperuserAuthService(users=[])
    router = build_router(auth=auth)

    bot = FakeBot()
    message = FakeMessage(user_id=900, bot=bot)
    state = FakeState()

    run(get_handler(router, "revoke_role_list_handler")(message, state, bot))

    assert message.answers[0]["text"] == SUPERUSER_REVOKE_ROLE_EMPTY_TEXT

def test_superuser_revoke_role_list_saves_message_ids():
    auth = FakeSuperuserAuthService(
        users=[
            FakeAuthUser(tg_id=10, roles=[Role.SUPERUSER, Role.EMPLOYEE]),
            FakeAuthUser(tg_id=20, roles=[Role.LEAD]),
        ]
    )
    bot = FakeBot(
        chats={
            10: FakeChatInfo(username="admin10"),
            20: FakeChatInfo(first_name="Lead20"),
        }
    )
    router = build_router(auth=auth)

    message = FakeMessage(user_id=900, bot=bot)
    patch_answer_return_message_id(message, start_id=2000)
    state = FakeState()

    run(get_handler(router, "revoke_role_list_handler")(message, state, bot))

    assert message.answers[0]["text"] == SUPERUSER_REVOKE_ROLE_LIST_TEXT

    data = run(state.get_data())
    assert "revoke_role_message_ids" in data
    assert len(data["revoke_role_message_ids"]) == 3

def test_superuser_revoke_unknown_role_alert():
    auth = FakeSuperuserAuthService(users=[FakeAuthUser(tg_id=10, roles=[Role.SUPERUSER])])
    bot = FakeBot(chats={10: FakeChatInfo(username="admin10")})
    router = build_router(auth=auth)

    msg = FakeMessage(user_id=900, bot=bot)
    cb = FakeCallback(data=f"{SUPERUSER_REVOKE_CALLBACK_PREFIX}:10:unknown", user_id=900, bot=bot, message=msg)

    run(get_handler(router, "revoke_role_callback", kind="callback_query")(cb, FakeState(), bot))

    assert cb.answers[-1]["show_alert"] is True
    assert "Неизвестная роль" in (cb.answers[-1]["text"] or "")

def test_superuser_revoke_last_superuser_blocked():
    auth = FakeSuperuserAuthService(
        users=[FakeAuthUser(tg_id=10, roles=[Role.SUPERUSER])],
        can_superuser={10: True},
    )
    bot = FakeBot(chats={10: FakeChatInfo(username="admin10")})
    router = build_router(auth=auth)

    msg = FakeMessage(user_id=900, bot=bot)
    cb = FakeCallback(data=f"{SUPERUSER_REVOKE_CALLBACK_PREFIX}:10:superuser", user_id=900, bot=bot, message=msg)

    run(get_handler(router, "revoke_role_callback", kind="callback_query")(cb, FakeState(), bot))

    assert cb.answers[-1]["show_alert"] is True
    assert cb.answers[-1]["text"] == SUPERUSER_REVOKE_ROLE_LAST_SUPERUSER
    assert auth.revoke_calls == []

def test_superuser_revoke_role_not_found_alert():
    auth = FakeSuperuserAuthService(
        users=[FakeAuthUser(tg_id=10, roles=[Role.SUPERUSER, Role.EMPLOYEE])],
        revoke_map={(10, Role.EMPLOYEE): False},
    )
    bot = FakeBot(chats={10: FakeChatInfo(username="admin10")})
    router = build_router(auth=auth)

    msg = FakeMessage(user_id=900, bot=bot)
    cb = FakeCallback(data=f"{SUPERUSER_REVOKE_CALLBACK_PREFIX}:10:employee", user_id=900, bot=bot, message=msg)

    run(get_handler(router, "revoke_role_callback", kind="callback_query")(cb, FakeState(), bot))

    assert cb.answers[-1]["show_alert"] is True
    assert cb.answers[-1]["text"] == SUPERUSER_REVOKE_ROLE_NOT_FOUND

def test_superuser_revoke_role_success_updates_message_and_deletes_other_messages():
    auth = FakeSuperuserAuthService(
        users=[FakeAuthUser(tg_id=10, roles=[Role.SUPERUSER, Role.EMPLOYEE])],
        can_superuser={10: True},
        revoke_map={(10, Role.EMPLOYEE): True},
        roles_after_revoke={10: [Role.SUPERUSER]},
    )
    bot = FakeBot(chats={10: FakeChatInfo(username="admin10")})
    deleted = []

    async def delete_message(chat_id: int, message_id: int):
        deleted.append((chat_id, message_id))

    bot.delete_message = delete_message

    router = build_router(auth=auth)
    state = FakeState({"revoke_role_message_ids": [101, 202, 303]})

    msg = FakeMessage(user_id=900, bot=bot, chat_id=500, message_id=202)
    cb = FakeCallback(
        data=f"{SUPERUSER_REVOKE_CALLBACK_PREFIX}:10:employee",
        user_id=900,
        bot=bot,
        message=msg,
    )

    run(get_handler(router, "revoke_role_callback", kind="callback_query")(cb, state, bot))

    assert auth.revoke_calls == [(10, Role.EMPLOYEE)]
    assert "Роли:" in msg.edits[-1]["text"]

    assert (500, 101) in deleted
    assert (500, 303) in deleted
    assert (500, 202) not in deleted

    data = run(state.get_data())
    assert data["revoke_role_message_ids"] == [202]

    assert cb.answers[-1]["text"] == SUPERUSER_REVOKE_ROLE_SUCCESS.format(role=Role.EMPLOYEE.title)

def test_superuser_revoke_role_success_when_no_roles_left():
    auth = FakeSuperuserAuthService(
        users=[FakeAuthUser(tg_id=10, roles=[Role.EMPLOYEE])],
        revoke_map={(10, Role.EMPLOYEE): True},
        roles_after_revoke={10: []},
    )
    bot = FakeBot(chats={10: FakeChatInfo(first_name="Bob")})

    async def delete_message(chat_id: int, message_id: int):
        return None

    bot.delete_message = delete_message

    router = build_router(auth=auth)
    state = FakeState({"revoke_role_message_ids": [55]})

    msg = FakeMessage(user_id=900, bot=bot, chat_id=500, message_id=55)
    cb = FakeCallback(
        data=f"{SUPERUSER_REVOKE_CALLBACK_PREFIX}:10:employee",
        user_id=900,
        bot=bot,
        message=msg,
    )

    run(get_handler(router, "revoke_role_callback", kind="callback_query")(cb, state, bot))

    assert "нет ролей" in msg.edits[-1]["text"].lower()

def test_superuser_ban_user_stub():
    router = build_router()
    message = FakeMessage(user_id=900)

    run(get_handler(router, "ban_user_handler")(message))

    assert message.answers[0]["text"] == BAN_USER_NOT_READY_TEXT
    assert Buttons.SUPERUSER_BAN_USER in message.answers[0]["reply_markup"].texts()
