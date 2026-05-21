from __future__ import annotations

import asyncio

from conftest import FakeBot, FakeChatInfo, FakeCallback, FakeMessage, FakeState, get_handler
from constants.bot_constants import Buttons
from constants.texts import (
    ACTION_CANCELLED_TEXT,
    BIND_MANAGER_INVALID_LEAD_TEXT,
    BIND_MANAGER_NO_LEADS_TEXT,
    BIND_MANAGER_REQUEST_SENT_TEXT,
    BIND_MANAGER_SELECT_TEXT,
    COMPLETE_TASK_TEXT,
    INTERN_TASKS_EMPTY_TEXT,
    INTERN_TASKS_LIST_TEXT,
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
    VISIT_FINISH_NO_OPEN_TEXT,
    VISIT_FINISH_SUCCESS_TEXT,
    VISIT_START_ALREADY_OPEN_TEXT,
    VISIT_START_SUCCESS_TEXT,
)
from handlers.intern import setup_intern_router
from keyboards.role_menus import TASK_CALLBACK_PREFIX
from roles import Role
from states.manager_binding import ManagerBindingStates
from states.task_report import TaskReportStates
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
    return setup_intern_router(
        auth_service=auth or FakeAuthService(),
        visits_service=visits or FakeVisitsService(),
        tasks_service=tasks or FakeTasksService(),
        reports_service=reports or FakeReportsService(),
        manager_binding_service=manager_binding or FakeManagerBindingService(),
        accepted_tasks_service=accepted or FakeAcceptedTasksService(),
        daily_reports_service=daily_reports or FakeDailyReportsService(),
    )


def test_start_work_success_and_already_open_for_intern():
    for service_result, expected_text in [
        (True, VISIT_START_SUCCESS_TEXT),
        (False, VISIT_START_ALREADY_OPEN_TEXT),
    ]:
        visits = FakeVisitsService(start_result=service_result)
        router = build_router(visits=visits)
        message = FakeMessage(user_id=301)

        run(get_handler(router, "start_work")(message))

        assert visits.started_for == [301]
        assert message.answers[0]["text"] == expected_text
        assert Buttons.INTERN_TASKS_LIST in message.answers[0]["reply_markup"].texts()


def test_finish_work_success_and_without_open_visit_for_intern():
    for service_result, expected_text in [
        (True, VISIT_FINISH_SUCCESS_TEXT),
        (False, VISIT_FINISH_NO_OPEN_TEXT),
    ]:
        visits = FakeVisitsService(finish_result=service_result)
        router = build_router(visits=visits)
        message = FakeMessage(user_id=301)

        run(get_handler(router, "finish_work")(message))

        assert visits.finished_for == [301]
        assert message.answers[0]["text"] == expected_text
        assert Buttons.INTERN_BIND_MANAGER in message.answers[0]["reply_markup"].texts()


def test_bind_manager_start_for_intern_shows_no_leads_or_available_leads():
    no_leads_router = build_router(auth=FakeAuthService(lead_ids=[]))
    no_leads_message = FakeMessage(user_id=300)
    no_leads_state = FakeState()

    run(get_handler(no_leads_router, "bind_manager_start")(no_leads_message, no_leads_state))

    assert no_leads_message.answers[0]["text"] == BIND_MANAGER_NO_LEADS_TEXT

    auth = FakeAuthService(lead_ids=[400], manager_ids_by_key={(300, Role.INTERN): []})
    router = build_router(auth=auth)
    bot = FakeBot(chats={400: FakeChatInfo(first_name="Роман")})
    message = FakeMessage(user_id=300, bot=bot)
    state = FakeState()

    run(get_handler(router, "bind_manager_start")(message, state))

    assert state.state is ManagerBindingStates.waiting_lead
    assert state.data["bind_lead_options"] == {"Роман": 400}
    assert message.answers[0]["text"] == BIND_MANAGER_SELECT_TEXT


def test_bind_manager_cancel_and_invalid_selection_for_intern():
    router = build_router()

    cancel_message = FakeMessage(text=Buttons.CANCEL)
    cancel_state = FakeState({"bind_lead_options": {"Lead": 400}})
    run(get_handler(router, "bind_manager_cancel")(cancel_message, cancel_state))
    assert cancel_state.clear_count == 1
    assert cancel_message.answers[0]["text"] == ACTION_CANCELLED_TEXT

    invalid_message = FakeMessage(text="Unknown")
    invalid_state = FakeState({"bind_lead_options": {"Lead": 400}})
    run(get_handler(router, "bind_manager_selected")(invalid_message, invalid_state))
    assert invalid_message.answers[0]["text"] == BIND_MANAGER_INVALID_LEAD_TEXT


def test_bind_manager_selected_for_intern_creates_request_with_intern_role():
    manager_binding = FakeManagerBindingService(create_result=object())
    router = build_router(manager_binding=manager_binding)
    message = FakeMessage(text="Lead", user_id=300)
    state = FakeState({"bind_lead_options": {"Lead": 400}})

    run(get_handler(router, "bind_manager_selected")(message, state))

    assert manager_binding.create_calls == [(300, Role.INTERN, 400)]
    assert state.clear_count == 1
    assert message.answers[0]["text"] == BIND_MANAGER_REQUEST_SENT_TEXT


def test_my_task_list_empty_for_intern():
    router = build_router(tasks=FakeTasksService([]))
    message = FakeMessage(user_id=300)

    run(get_handler(router, "my_task_list")(message))

    assert message.answers[0]["text"] == INTERN_TASKS_EMPTY_TEXT


def test_my_task_list_for_intern_renders_tasks_and_feedback():
    tasks = FakeTasksService(
        [
            make_task("active", employee_id=300, author_id=400, status="in process", title="Практика"),
            make_task("cancelled", employee_id=300, author_id=400, status="cancelled", title="Переделать"),
            make_task("ignored", employee_id=300, author_id=400, status="on consideration", title="Не показывать"),
        ]
    )
    reports = FakeReportsService(feedback_by_task={"cancelled": "замечание"})
    bot = FakeBot(chats={400: FakeChatInfo(username="lead")})
    router = build_router(tasks=tasks, reports=reports)
    message = FakeMessage(user_id=300, bot=bot)

    run(get_handler(router, "my_task_list")(message))

    assert message.answers[0]["text"] == INTERN_TASKS_LIST_TEXT
    rendered = "\n".join(answer["text"] for answer in message.answers[1:])
    assert "Практика" in rendered
    assert "Переделать" in rendered
    assert "Не показывать" not in rendered
    assert "Комментарий руководителя" in rendered
    assert "@lead" in rendered


def test_process_task_action_accept_finish_report_and_guard_cases_for_intern():
    accept_tasks = FakeTasksService([make_task("a", employee_id=300, status="created")])
    accept_router = build_router(tasks=accept_tasks)
    accept_callback = FakeCallback(data=f"{TASK_CALLBACK_PREFIX}:accept:a", user_id=300)
    run(get_handler(accept_router, "process_task_action")(accept_callback, FakeState()))
    assert accept_tasks.update_calls == [("a", "in process")]
    assert accept_callback.answers[0]["text"] == TASK_ACCEPT_SUCCESS_TEXT

    finish_tasks = FakeTasksService([make_task("f", employee_id=300, status="in process")])
    finish_router = build_router(tasks=finish_tasks)
    finish_callback = FakeCallback(data=f"{TASK_CALLBACK_PREFIX}:finish:f", user_id=300)
    run(get_handler(finish_router, "process_task_action")(finish_callback, FakeState()))
    assert finish_tasks.update_calls == [("f", "finished")]
    assert finish_callback.answers[0]["text"] == TASK_FINISH_SUCCESS_TEXT

    report_tasks = FakeTasksService([make_task("r", employee_id=300, status="finished")])
    report_router = build_router(tasks=report_tasks)
    report_message = FakeMessage(user_id=300, chat_id=900, message_id=44)
    report_callback = FakeCallback(data=f"{TASK_CALLBACK_PREFIX}:report:r", user_id=300, message=report_message)
    report_state = FakeState({"old": "data"})
    run(get_handler(report_router, "process_task_action")(report_callback, report_state))
    assert report_state.state is TaskReportStates.waiting_report_text
    assert report_state.data == {"report_task_id": "r", "report_msg_chat_id": 900, "report_msg_id": 44}
    assert report_message.answers[0]["text"] == REPORT_TEXT_PROMPT

    missing_router = build_router(tasks=FakeTasksService([]))
    missing_callback = FakeCallback(data=f"{TASK_CALLBACK_PREFIX}:accept:nope", user_id=300)
    run(get_handler(missing_router, "process_task_action")(missing_callback, FakeState()))
    assert missing_callback.answers[0]["text"] == TASK_NOT_FOUND_TEXT
    assert missing_callback.answers[0]["show_alert"] is True

    foreign_router = build_router(tasks=FakeTasksService([make_task("x", employee_id=777, status="created")]))
    foreign_callback = FakeCallback(data=f"{TASK_CALLBACK_PREFIX}:accept:x", user_id=300)
    run(get_handler(foreign_router, "process_task_action")(foreign_callback, FakeState()))
    assert foreign_callback.answers[0]["text"] == TASK_ACTION_NOT_ALLOWED_TEXT


def test_complete_task_report_comment_and_report_cancel_for_intern():
    router = build_router()

    complete_message = FakeMessage(text=Buttons.INTERN_COMPLETE_TASK)
    run(get_handler(router, "complete_task")(complete_message))
    assert complete_message.answers[0]["text"] == COMPLETE_TASK_TEXT

    comment_message = FakeMessage(text=Buttons.INTERN_REPORT_COMMENT)
    run(get_handler(router, "report_comment")(comment_message))
    assert comment_message.answers[0]["text"] == REPORT_COMMENT_TEXT

    cancel_state = FakeState({"report_task_id": "r"})
    cancel_message = FakeMessage(text=Buttons.CANCEL)
    run(get_handler(router, "report_cancel")(cancel_message, cancel_state))
    assert cancel_state.clear_count == 1
    assert cancel_message.answers[0]["text"] == ACTION_CANCELLED_TEXT


def test_report_send_for_intern_rejects_empty_and_successfully_sends_report():
    empty_router = build_router()
    empty_message = FakeMessage(text="  ", user_id=300)
    empty_state = FakeState({"report_task_id": "r"})
    run(get_handler(empty_router, "report_send")(empty_message, empty_state))
    assert empty_message.answers[0]["text"] == REPORT_EMPTY_TEXT
    assert empty_state.clear_count == 0

    tasks = FakeTasksService([make_task("r", employee_id=300, author_id=400, status="in process")])
    reports = FakeReportsService()
    bot = FakeBot(chats={400: FakeChatInfo(username="mentor")})
    router = build_router(tasks=tasks, reports=reports)
    message = FakeMessage(text="Выполнено", user_id=300, bot=bot)
    state = FakeState({"report_task_id": "r", "report_msg_chat_id": 900, "report_msg_id": 44})

    run(get_handler(router, "report_send")(message, state))

    assert tasks.update_calls == [("r", "on consideration")]
    assert reports.created_reports == [("r", 300, "Выполнено")]
    assert bot.edited_messages[0]["chat_id"] == 900
    assert message.answers[0]["text"] == REPORT_SENT_TEXT
    assert state.clear_count == 1


def test_daily_report_flow_saves_intern_answers_and_task_snapshot():
    tasks = FakeTasksService([
        make_task("done", employee_id=300, status="finished", title="Сделанная задача", updated_at="2026-05-17 13:00:00"),
        make_task("progress", employee_id=300, status="in process", title="Практика в работе"),
        make_task("foreign", employee_id=301, status="finished", title="Чужая", updated_at="2026-05-17 13:00:00"),
    ])
    accepted = FakeAcceptedTasksService(titles_by_key={(300, "2026-05-17"): ["Уже принятая"]})
    daily_reports = FakeDailyReportsService(today="2026-05-17", was_updated=False)
    router = build_router(tasks=tasks, accepted=accepted, daily_reports=daily_reports)
    state = FakeState({"old": "data"})

    start_message = FakeMessage(text=Buttons.INTERN_DAILY_REPORT, user_id=300)
    run(get_handler(router, "daily_report_start")(start_message, state))
    assert state.clear_count == 1
    assert state.state is DailyReportStates.waiting_work_done
    assert start_message.answers[0]["text"] == DAILY_REPORT_WORK_DONE_PROMPT

    work_message = FakeMessage(text="Изучал проект", user_id=300)
    run(get_handler(router, "daily_report_work_done")(work_message, state))
    assert state.state is DailyReportStates.waiting_problems
    assert work_message.answers[0]["text"] == DAILY_REPORT_PROBLEMS_PROMPT

    problems_message = FakeMessage(text="Не хватило доступов", user_id=300)
    run(get_handler(router, "daily_report_problems")(problems_message, state))

    assert daily_reports.create_calls == [
        (
            300,
            "2026-05-17",
            "Изучал проект",
            "Не хватило доступов",
            ["Сделанная задача", "Уже принятая"],
            ["Практика в работе"],
        )
    ]
    assert state.clear_count == 2
    assert problems_message.answers[0]["text"] == DAILY_REPORT_SAVED_TEXT


def test_daily_report_for_intern_validates_empty_problem_and_shows_updated_text():
    daily_reports = FakeDailyReportsService(today="2026-05-17", was_updated=True)
    router = build_router(daily_reports=daily_reports)
    state = FakeState({"daily_work_done": "Повторно описал день"})

    empty_message = FakeMessage(text="  ", user_id=300)
    run(get_handler(router, "daily_report_problems")(empty_message, state))
    assert empty_message.answers[0]["text"] == DAILY_REPORT_EMPTY_TEXT
    assert daily_reports.create_calls == []

    message = FakeMessage(text="-", user_id=300)
    run(get_handler(router, "daily_report_problems")(message, state))
    assert daily_reports.create_calls[0][3] == ""
    assert message.answers[0]["text"] == DAILY_REPORT_UPDATED_TEXT


def test_report_comment_button_shows_cancelled_task_feedback_for_intern():
    tasks = FakeTasksService([
        make_task("cancelled", employee_id=300, status="cancelled", title="Переделать <модуль>"),
        make_task("active", employee_id=300, status="finished", title="Не показывать"),
    ])
    reports = FakeReportsService(feedback_by_task={"cancelled": "замечание <важно>"})
    router = build_router(tasks=tasks, reports=reports)
    message = FakeMessage(text=Buttons.INTERN_REPORT_COMMENT, user_id=300)

    run(get_handler(router, "report_comment")(message))

    rendered = message.answers[0]["text"]
    assert rendered.startswith(REPORT_COMMENT_TEXT)
    assert "Переделать &lt;модуль&gt;" in rendered
    assert "замечание &lt;важно&gt;" in rendered
    assert "Не показывать" not in rendered
    assert message.answers[0]["parse_mode"] == "HTML"
