from __future__ import annotations

import asyncio
from types import SimpleNamespace

from conftest import FakeBot, FakeChatInfo, FakeCallback, FakeMessage, FakeState, get_handler
from constants.bot_constants import Buttons
from constants.texts import (
    ACTION_CANCELLED_TEXT,
    BIND_MANAGER_ALREADY_BOUND_TEXT,
    BIND_MANAGER_INVALID_LEAD_TEXT,
    BIND_MANAGER_NO_LEADS_TEXT,
    BIND_MANAGER_REQUEST_ALREADY_EXISTS_TEXT,
    BIND_MANAGER_REQUEST_SENT_TEXT,
    BIND_MANAGER_SELECT_TEXT,
    COMPLETE_TASK_TEXT,
    EMPLOYEE_TASKS_EMPTY_TEXT,
    EMPLOYEE_TASKS_LIST_TEXT,
    OFFER_TASK_TITLE_PROMPT,
    REPORT_COMMENT_TEXT,
    REPORT_EMPTY_TEXT,
    REPORT_SENT_TEXT,
    REPORT_TEXT_PROMPT,
    DAILY_REPORT_EMPTY_TEXT,
    DAILY_REPORT_PROBLEMS_PROMPT,
    DAILY_REPORT_SAVED_TEXT,
    DAILY_REPORT_UPDATED_TEXT,
    DAILY_REPORT_WORK_DONE_PROMPT,
    TASK_ACCEPT_SUCCESS_TEXT,
    TASK_ACTION_NOT_ALLOWED_TEXT,
    TASK_FINISH_SUCCESS_TEXT,
    TASK_NOT_FOUND_TEXT,
    TASK_STATUS_ALREADY_CHANGED_TEXT,
    VISIT_FINISH_NO_OPEN_TEXT,
    VISIT_FINISH_SUCCESS_TEXT,
    VISIT_START_ALREADY_OPEN_TEXT,
    VISIT_START_SUCCESS_TEXT,
)
from handlers.employee import setup_employee_router
from keyboards.role_menus import TASK_CALLBACK_PREFIX
from roles import Role
from states.manager_binding import ManagerBindingStates
from states.task_report import TaskReportStates
from states.task_request import TaskRequestStates
from states.daily_report import DailyReportStates

from helpers import (
    FakeAuthService,
    FakeManagerBindingService,
    FakeAcceptedTasksService,
    FakeDailyReportsService,
    FakeReportsService,
    FakeTasksService,
    FakeVisitsService,
    make_task,
)


def run(coro):
    return asyncio.run(coro)


def build_router(
    *,
    auth=None,
    visits=None,
    tasks=None,
    reports=None,
    manager_binding=None,
    accepted=None,
    daily_reports=None,
):
    return setup_employee_router(
        auth_service=auth or FakeAuthService(),
        visits_service=visits or FakeVisitsService(),
        tasks_service=tasks or FakeTasksService(),
        reports_service=reports or FakeReportsService(),
        manager_binding_service=manager_binding or FakeManagerBindingService(),
        accepted_tasks_service=accepted or FakeAcceptedTasksService(),
        daily_reports_service=daily_reports or FakeDailyReportsService(),
    )


def test_start_work_success_and_already_open():
    for service_result, expected_text in [
        (True, VISIT_START_SUCCESS_TEXT),
        (False, VISIT_START_ALREADY_OPEN_TEXT),
    ]:
        visits = FakeVisitsService(start_result=service_result)
        router = build_router(visits=visits)
        message = FakeMessage(user_id=101)

        run(get_handler(router, "start_work")(message))

        assert visits.started_for == [101]
        assert message.answers[0]["text"] == expected_text
        assert Buttons.EMPLOYEE_TASKS_LIST in message.answers[0]["reply_markup"].texts()


def test_finish_work_success_and_without_open_visit():
    for service_result, expected_text in [
        (True, VISIT_FINISH_SUCCESS_TEXT),
        (False, VISIT_FINISH_NO_OPEN_TEXT),
    ]:
        visits = FakeVisitsService(finish_result=service_result)
        router = build_router(visits=visits)
        message = FakeMessage(user_id=101)

        run(get_handler(router, "finish_work")(message))

        assert visits.finished_for == [101]
        assert message.answers[0]["text"] == expected_text
        assert Buttons.EMPLOYEE_BIND_MANAGER in message.answers[0]["reply_markup"].texts()


def test_create_my_task_starts_task_offer_flow():
    router = build_router()
    message = FakeMessage(text=Buttons.EMPLOYEE_CREATE_TASK)
    state = FakeState({"old": "data"})

    run(get_handler(router, "create_my_task")(message, state))

    assert state.clear_count == 1
    assert state.state is TaskRequestStates.waiting_title
    assert message.answers[0]["text"] == OFFER_TASK_TITLE_PROMPT
    assert message.answers[0]["reply_markup"].texts() == [Buttons.CANCEL]


def test_bind_manager_start_shows_no_leads_when_none_available():
    router = build_router(auth=FakeAuthService(lead_ids=[]))
    message = FakeMessage(user_id=100)
    state = FakeState()

    run(get_handler(router, "bind_manager_start")(message, state))

    assert state.clear_count == 1
    assert message.answers[0]["text"] == BIND_MANAGER_NO_LEADS_TEXT


def test_bind_manager_start_excludes_current_and_existing_managers_then_prompts():
    auth = FakeAuthService(
        lead_ids=[100, 200, 201],
        manager_ids_by_key={(100, Role.EMPLOYEE): [201]},
    )
    router = build_router(auth=auth)
    bot = FakeBot(chats={200: FakeChatInfo(username="lead_one")})
    message = FakeMessage(user_id=100, bot=bot)
    state = FakeState()

    run(get_handler(router, "bind_manager_start")(message, state))

    assert state.state is ManagerBindingStates.waiting_lead
    assert state.data["bind_lead_options"] == {"@lead_one": 200}
    assert message.answers[0]["text"] == BIND_MANAGER_SELECT_TEXT
    assert message.answers[0]["reply_markup"].texts() == ["@lead_one", Buttons.CANCEL]


def test_bind_manager_start_reports_all_leads_already_bound():
    auth = FakeAuthService(
        lead_ids=[200, 201],
        manager_ids_by_key={(100, Role.EMPLOYEE): [200, 201]},
    )
    router = build_router(auth=auth)
    message = FakeMessage(user_id=100)
    state = FakeState()

    run(get_handler(router, "bind_manager_start")(message, state))

    assert message.answers[0]["text"] == BIND_MANAGER_ALREADY_BOUND_TEXT


def test_bind_manager_cancel_clears_state_and_returns_to_menu():
    router = build_router()
    message = FakeMessage(text=Buttons.CANCEL)
    state = FakeState({"bind_lead_options": {"Lead": 200}})

    run(get_handler(router, "bind_manager_cancel")(message, state))

    assert state.clear_count == 1
    assert message.answers[0]["text"] == ACTION_CANCELLED_TEXT
    assert Buttons.EMPLOYEE_BIND_MANAGER in message.answers[0]["reply_markup"].texts()


def test_bind_manager_selected_rejects_unknown_option():
    router = build_router()
    message = FakeMessage(text="Unknown")
    state = FakeState({"bind_lead_options": {"Lead": 200}})

    run(get_handler(router, "bind_manager_selected")(message, state))

    assert message.answers[0]["text"] == BIND_MANAGER_INVALID_LEAD_TEXT
    assert message.answers[0]["reply_markup"].texts() == ["Lead", Buttons.CANCEL]


def test_bind_manager_selected_rejects_self_binding():
    router = build_router()
    message = FakeMessage(text="Myself", user_id=100)
    state = FakeState({"bind_lead_options": {"Myself": 100}})

    run(get_handler(router, "bind_manager_selected")(message, state))

    assert message.answers[0]["text"] == BIND_MANAGER_INVALID_LEAD_TEXT


def test_bind_manager_selected_detects_existing_manager():
    auth = FakeAuthService(manager_ids_by_key={(100, Role.EMPLOYEE): [200]})
    router = build_router(auth=auth)
    message = FakeMessage(text="Lead", user_id=100)
    state = FakeState({"bind_lead_options": {"Lead": 200}})

    run(get_handler(router, "bind_manager_selected")(message, state))

    assert state.clear_count == 1
    assert message.answers[0]["text"] == BIND_MANAGER_ALREADY_BOUND_TEXT


def test_bind_manager_selected_sends_request_or_reports_duplicate():
    for create_result, expected_text in [
        (object(), BIND_MANAGER_REQUEST_SENT_TEXT),
        (None, BIND_MANAGER_REQUEST_ALREADY_EXISTS_TEXT),
    ]:
        manager_binding = FakeManagerBindingService(create_result=create_result)
        router = build_router(manager_binding=manager_binding)
        message = FakeMessage(text="Lead", user_id=100)
        state = FakeState({"bind_lead_options": {"Lead": 200}})

        run(get_handler(router, "bind_manager_selected")(message, state))

        assert manager_binding.create_calls == [(100, Role.EMPLOYEE, 200)]
        assert state.clear_count == 1
        assert message.answers[0]["text"] == expected_text


def test_my_task_list_empty():
    router = build_router(tasks=FakeTasksService([]))
    message = FakeMessage(user_id=100)

    run(get_handler(router, "my_task_list")(message))

    assert message.answers[0]["text"] == EMPLOYEE_TASKS_EMPTY_TEXT


def test_my_task_list_outputs_allowed_statuses_and_manager_feedback():
    tasks = FakeTasksService(
        [
            make_task("created", status="created", title="Новая"),
            make_task("hidden", status="on consideration", title="Скрытая"),
            make_task("cancelled", status="cancelled", title="Вернуть", description="Исправить"),
        ]
    )
    reports = FakeReportsService(feedback_by_task={"cancelled": "<переделать>"})
    bot = FakeBot(chats={200: FakeChatInfo(full_name="Иван Руководитель")})
    router = build_router(tasks=tasks, reports=reports)
    message = FakeMessage(user_id=100, bot=bot)

    run(get_handler(router, "my_task_list")(message))

    assert [answer["text"] for answer in message.answers][:1] == [EMPLOYEE_TASKS_LIST_TEXT]
    rendered_tasks = "\n---\n".join(answer["text"] for answer in message.answers[1:])
    assert "Новая" in rendered_tasks
    assert "Вернуть" in rendered_tasks
    assert "Скрытая" not in rendered_tasks
    assert "&lt;переделать&gt;" in rendered_tasks
    assert all(answer.get("parse_mode") == "HTML" for answer in message.answers[1:])


def test_process_task_action_accepts_created_task():
    tasks = FakeTasksService([make_task("t1", status="created")])
    router = build_router(tasks=tasks)
    bot = FakeBot(chats={200: FakeChatInfo(username="boss")})
    message = FakeMessage(bot=bot)
    callback = FakeCallback(data=f"{TASK_CALLBACK_PREFIX}:accept:t1", user_id=100, bot=bot, message=message)
    state = FakeState()

    run(get_handler(router, "process_task_action")(callback, state))

    assert tasks.update_calls == [("t1", "in process")]
    assert callback.answers[0]["text"] == TASK_ACCEPT_SUCCESS_TEXT
    assert message.edits and "<b>Руководитель:</b> @boss" in message.edits[0]["text"]


def test_process_task_action_finishes_task_in_process():
    tasks = FakeTasksService([make_task("t1", status="in process")])
    router = build_router(tasks=tasks)
    callback = FakeCallback(data=f"{TASK_CALLBACK_PREFIX}:finish:t1", user_id=100)
    state = FakeState()

    run(get_handler(router, "process_task_action")(callback, state))

    assert tasks.update_calls == [("t1", "finished")]
    assert callback.answers[0]["text"] == TASK_FINISH_SUCCESS_TEXT


def test_process_task_action_opens_report_state_for_allowed_status():
    tasks = FakeTasksService([make_task("t1", status="finished")])
    router = build_router(tasks=tasks)
    message = FakeMessage(chat_id=777, message_id=33)
    callback = FakeCallback(data=f"{TASK_CALLBACK_PREFIX}:report:t1", user_id=100, message=message)
    state = FakeState({"old": "value"})

    run(get_handler(router, "process_task_action")(callback, state))

    assert state.clear_count == 1
    assert state.state is TaskReportStates.waiting_report_text
    assert state.data == {"report_task_id": "t1", "report_msg_chat_id": 777, "report_msg_id": 33}
    assert message.answers[0]["text"] == REPORT_TEXT_PROMPT
    assert callback.answers[0]["text"] is None


def test_process_task_action_validates_task_existence_owner_status_and_action():
    cases = [
        ([], f"{TASK_CALLBACK_PREFIX}:accept:missing", TASK_NOT_FOUND_TEXT, True),
        ([make_task("t1", employee_id=999)], f"{TASK_CALLBACK_PREFIX}:accept:t1", TASK_ACTION_NOT_ALLOWED_TEXT, True),
        ([make_task("t1", status="in process")], f"{TASK_CALLBACK_PREFIX}:accept:t1", TASK_STATUS_ALREADY_CHANGED_TEXT, True),
        ([make_task("t1", status="created")], f"{TASK_CALLBACK_PREFIX}:finish:t1", TASK_STATUS_ALREADY_CHANGED_TEXT, True),
        ([make_task("t1", status="created")], f"{TASK_CALLBACK_PREFIX}:report:t1", TASK_ACTION_NOT_ALLOWED_TEXT, True),
        ([make_task("t1", status="created")], f"{TASK_CALLBACK_PREFIX}:unknown:t1", TASK_ACTION_NOT_ALLOWED_TEXT, True),
    ]

    for task_list, callback_data, expected_text, expected_alert in cases:
        router = build_router(tasks=FakeTasksService(task_list))
        callback = FakeCallback(data=callback_data, user_id=100)
        state = FakeState()

        run(get_handler(router, "process_task_action")(callback, state))

        assert callback.answers[0]["text"] == expected_text
        assert callback.answers[0]["show_alert"] is expected_alert


def test_complete_task_and_report_comment_buttons_return_stub_texts():
    router = build_router()

    complete_message = FakeMessage(text=Buttons.EMPLOYEE_COMPLETE_TASK)
    run(get_handler(router, "complete_task")(complete_message))
    assert complete_message.answers[0]["text"] == COMPLETE_TASK_TEXT

    comment_message = FakeMessage(text=Buttons.EMPLOYEE_REPORT_COMMENT)
    run(get_handler(router, "report_comment")(comment_message))
    assert comment_message.answers[0]["text"] == REPORT_COMMENT_TEXT


def test_report_cancel_clears_state_and_returns_to_menu():
    router = build_router()
    message = FakeMessage(text=Buttons.CANCEL)
    state = FakeState({"report_task_id": "t1"})

    run(get_handler(router, "report_cancel")(message, state))

    assert state.clear_count == 1
    assert message.answers[0]["text"] == ACTION_CANCELLED_TEXT


def test_report_send_rejects_empty_text():
    router = build_router()
    message = FakeMessage(text="   ")
    state = FakeState({"report_task_id": "t1"})

    run(get_handler(router, "report_send")(message, state))

    assert state.clear_count == 0
    assert message.answers[0]["text"] == REPORT_EMPTY_TEXT


def test_report_send_handles_missing_task_id_missing_task_and_foreign_task():
    scenarios = [
        (FakeState({}), FakeTasksService([]), TASK_NOT_FOUND_TEXT),
        (FakeState({"report_task_id": "missing"}), FakeTasksService([]), TASK_NOT_FOUND_TEXT),
        (FakeState({"report_task_id": "t1"}), FakeTasksService([make_task("t1", employee_id=999)]), TASK_ACTION_NOT_ALLOWED_TEXT),
    ]

    for state, tasks, expected_text in scenarios:
        router = build_router(tasks=tasks)
        message = FakeMessage(text="Готово", user_id=100)

        run(get_handler(router, "report_send")(message, state))

        assert state.clear_count == 1
        assert message.answers[0]["text"] == expected_text


def test_report_send_updates_task_creates_report_edits_original_message_and_confirms():
    tasks = FakeTasksService([make_task("t1", status="in process")])
    reports = FakeReportsService()
    bot = FakeBot(chats={200: FakeChatInfo(username="boss")})
    router = build_router(tasks=tasks, reports=reports)
    message = FakeMessage(text="Работа выполнена", user_id=100, bot=bot)
    state = FakeState({"report_task_id": "t1", "report_msg_chat_id": 777, "report_msg_id": 33})

    run(get_handler(router, "report_send")(message, state))

    assert tasks.update_calls == [("t1", "on consideration")]
    assert reports.created_reports == [("t1", 100, "Работа выполнена")]
    assert bot.edited_messages[0]["chat_id"] == 777
    assert bot.edited_messages[0]["message_id"] == 33
    assert "@boss" in bot.edited_messages[0]["text"]
    assert state.clear_count == 1
    assert message.answers[0]["text"] == REPORT_SENT_TEXT


def test_daily_report_flow_saves_employee_answers_and_task_snapshot():
    tasks = FakeTasksService([
        make_task("done", status="finished", title="Готовая <задача>", updated_at="2026-05-17 15:00:00"),
        make_task("consider", status="on consideration", title="На проверке", updated_at="2026-05-17 16:00:00"),
        make_task("old", status="finished", title="Вчерашняя", updated_at="2026-05-16 18:00:00"),
        make_task("progress", status="in process", title="В работе"),
        make_task("created", status="created", title="Не считать"),
    ])
    accepted = FakeAcceptedTasksService(
        titles_by_key={(100, "2026-05-17"): ["Принятая", "Готовая <задача>"]}
    )
    daily_reports = FakeDailyReportsService(today="2026-05-17", was_updated=False)
    router = build_router(tasks=tasks, accepted=accepted, daily_reports=daily_reports)
    state = FakeState({"old": "data"})

    start_message = FakeMessage(text=Buttons.EMPLOYEE_DAILY_REPORT, user_id=100)
    run(get_handler(router, "daily_report_start")(start_message, state))
    assert state.clear_count == 1
    assert state.state is DailyReportStates.waiting_work_done
    assert start_message.answers[0]["text"] == DAILY_REPORT_WORK_DONE_PROMPT

    empty_message = FakeMessage(text="  ", user_id=100)
    run(get_handler(router, "daily_report_work_done")(empty_message, state))
    assert state.state is DailyReportStates.waiting_work_done
    assert empty_message.answers[0]["text"] == DAILY_REPORT_EMPTY_TEXT

    work_message = FakeMessage(text="Сделал интеграцию", user_id=100)
    run(get_handler(router, "daily_report_work_done")(work_message, state))
    assert state.state is DailyReportStates.waiting_problems
    assert state.data["daily_work_done"] == "Сделал интеграцию"
    assert work_message.answers[0]["text"] == DAILY_REPORT_PROBLEMS_PROMPT

    problems_message = FakeMessage(text="-", user_id=100)
    run(get_handler(router, "daily_report_problems")(problems_message, state))

    assert tasks.completed_calls == [(100, "2026-05-17")]
    assert accepted.title_calls == [(100, "2026-05-17")]
    assert tasks.in_process_calls == [100]
    assert daily_reports.create_calls == [
        (
            100,
            "2026-05-17",
            "Сделал интеграцию",
            "",
            ["На проверке", "Готовая <задача>", "Принятая"],
            ["В работе"],
        )
    ]
    assert state.clear_count == 2
    assert problems_message.answers[0]["text"] == DAILY_REPORT_SAVED_TEXT


def test_daily_report_cancel_and_update_text_for_employee():
    updated_daily_reports = FakeDailyReportsService(today="2026-05-17", was_updated=True)
    router = build_router(
        tasks=FakeTasksService([make_task("progress", status="in process", title="Текущая")]),
        daily_reports=updated_daily_reports,
    )

    cancel_state = FakeState()
    cancel_message = FakeMessage(text=Buttons.CANCEL, user_id=100)
    run(get_handler(router, "daily_report_cancel")(cancel_message, cancel_state))
    assert cancel_state.clear_count == 1
    assert cancel_message.answers[0]["text"] == ACTION_CANCELLED_TEXT

    state = FakeState({"daily_work_done": "Повторный отчет"})
    message = FakeMessage(text="Блокеров нет", user_id=100)
    run(get_handler(router, "daily_report_problems")(message, state))
    assert updated_daily_reports.create_calls[0][3] == "Блокеров нет"
    assert message.answers[0]["text"] == DAILY_REPORT_UPDATED_TEXT


def test_report_comment_button_shows_cancelled_task_feedback_for_employee():
    tasks = FakeTasksService([
        make_task("cancelled", status="cancelled", title="Вернуть <задачу>"),
        make_task("no-feedback", status="cancelled", title="Без комментария"),
        make_task("active", status="in process", title="Не показывать"),
    ])
    reports = FakeReportsService(feedback_by_task={"cancelled": "<исправить>"})
    router = build_router(tasks=tasks, reports=reports)
    message = FakeMessage(text=Buttons.EMPLOYEE_REPORT_COMMENT, user_id=100)

    run(get_handler(router, "report_comment")(message))

    rendered = message.answers[0]["text"]
    assert rendered.startswith(REPORT_COMMENT_TEXT)
    assert "Вернуть &lt;задачу&gt;" in rendered
    assert "&lt;исправить&gt;" in rendered
    assert "Без комментария" not in rendered
    assert "Не показывать" not in rendered
    assert message.answers[0]["parse_mode"] == "HTML"
