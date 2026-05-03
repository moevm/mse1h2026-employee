from __future__ import annotations

import asyncio

from conftest import FakeMessage, FakeState, get_handler
from constants.bot_constants import Buttons
from constants.texts import (
    ACTION_CANCELLED_TEXT,
    OFFER_TASK_DESCRIPTION_PROMPT,
    OFFER_TASK_NO_MANAGERS_TEXT,
    OFFER_TASK_SUCCESS_TEXT,
    OFFER_TASK_TITLE_PROMPT,
)
from handlers.task_request import setup_task_request_router
from roles import Role
from states.task_request import TaskRequestStates

from helpers import FakeAuthService, FakeTaskRequestService


def run(coro):
    return asyncio.run(coro)


def build_router(*, auth=None, task_request=None):
    return setup_task_request_router(
        auth_service=auth or FakeAuthService(),
        task_request_service=task_request or FakeTaskRequestService(),
    )


def test_offer_task_cancel_clears_state_and_returns_to_employee_menu():
    router = build_router()
    state = FakeState({"title": "Черновик"})
    message = FakeMessage(text=Buttons.CANCEL, user_id=100)

    run(get_handler(router, "offer_task_cancel")(message, state))

    assert state.clear_count == 1
    assert message.answers[0]["text"] == ACTION_CANCELLED_TEXT
    assert Buttons.EMPLOYEE_TASKS_LIST in message.answers[0]["reply_markup"].texts()


def test_offer_task_title_reprompts_on_empty_title():
    router = build_router()
    state = FakeState()
    message = FakeMessage(text="   ", user_id=100)

    run(get_handler(router, "offer_task_title")(message, state))

    assert state.update_calls == []
    assert state.state is None
    assert message.answers[0]["text"] == OFFER_TASK_TITLE_PROMPT


def test_offer_task_title_saves_title_and_asks_for_description():
    router = build_router()
    state = FakeState()
    message = FakeMessage(text="Новая функция", user_id=100)

    run(get_handler(router, "offer_task_title")(message, state))

    assert state.data == {"title": "Новая функция"}
    assert state.state is TaskRequestStates.waiting_description
    assert message.answers[0]["text"] == OFFER_TASK_DESCRIPTION_PROMPT
    assert message.answers[0]["reply_markup"].texts() == [Buttons.CANCEL]


def test_offer_task_description_reprompts_on_empty_description():
    router = build_router()
    state = FakeState({"title": "Новая задача"})
    message = FakeMessage(text="   ", user_id=100)

    run(get_handler(router, "offer_task_description")(message, state))

    assert state.clear_count == 0
    assert message.answers[0]["text"] == OFFER_TASK_DESCRIPTION_PROMPT


def test_offer_task_description_requires_at_least_one_manager():
    auth = FakeAuthService(manager_ids_by_key={(100, Role.EMPLOYEE): []})
    router = build_router(auth=auth)
    state = FakeState({"title": "Новая задача"})
    message = FakeMessage(text="Описание", user_id=100)

    run(get_handler(router, "offer_task_description")(message, state))

    assert state.clear_count == 1
    assert message.answers[0]["text"] == OFFER_TASK_NO_MANAGERS_TEXT


def test_offer_task_description_creates_requests_for_bound_managers():
    auth = FakeAuthService(manager_ids_by_key={(100, Role.EMPLOYEE): [200, 201]})
    task_request = FakeTaskRequestService()
    router = build_router(auth=auth, task_request=task_request)
    state = FakeState({"title": "Новая задача"})
    message = FakeMessage(text="Описание задачи", user_id=100)

    run(get_handler(router, "offer_task_description")(message, state))

    assert task_request.create_calls == [("Новая задача", "Описание задачи", [200, 201], 100)]
    assert state.clear_count == 1
    assert message.answers[0]["text"] == OFFER_TASK_SUCCESS_TEXT
    assert Buttons.EMPLOYEE_CREATE_TASK in message.answers[0]["reply_markup"].texts()
