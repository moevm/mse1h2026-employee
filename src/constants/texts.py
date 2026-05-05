WELCOME_TEXT = "Добро пожаловать!\nВыберите действие:"

NO_ROLES_TEXT = (
    "Для вашего Telegram ID роли не найдены.\n"
    "Нажмите «Получение роли», чтобы отправить запрос."
)

CHOOSE_ROLE_TEXT = "Выберите роль для входа:"
UNKNOWN_ROLE_TEXT = "Неизвестная роль"
NO_ACCESS_ROLE_TEXT = "У вас нет доступа к этой роли"
ROLE_SELECTED_TEXT = "Вы выбрали роль: {role}"
ROLE_REQUEST_NOT_READY_TEXT = "Раздел получения роли пока не реализован."
LOGOUT_TEXT = "Вы вышли в меню выбора ролей."

SUPERUSER_MENU_TEXT = "Ваша роль: суперпользователь\n\nВыберите действие:"

LEAD_MENU_TEXT = "Ваша роль: руководитель\n\nВыберите раздел:"

LEAD_TASKS_TEXT = "Задачи\n\nВыберите действие с задачами."

LEAD_REPORTS_TEXT = "Отчеты\n\nВыберите действие с отчетами."

LEAD_WEEKLY_TEXT = "Недельный отчет\n\nВведите сотрудника одним сообщением."

EMPLOYEE_MENU_TEXT = "Ваша роль: сотрудник\n\nВыберите действие:"

INTERN_MENU_TEXT = "Ваша роль: стажер\n\nВыберите действие:"

ROLE_REQUESTS_NOT_READY_TEXT = "Список запросов ролей пока не реализован."
CONFIRM_ROLE_NOT_READY_TEXT = "Подтверждение роли пока не реализовано."
BAN_USER_NOT_READY_TEXT = "Блокировка пользователя пока не реализована."

START_WORK_TEXT = "Начало рабочего дня пока реализовано как заглушка."
FINISH_WORK_TEXT = "Завершение рабочего дня пока реализовано как заглушка."
CREATE_MY_TASK_TEXT = "Создание личной задачи пока реализовано как заглушка."
MY_TASKS_TEXT = "Список задач пока реализован как заглушка."
COMPLETE_TASK_TEXT = "Отправка отчета пока реализована как заглушка."
REPORT_COMMENT_TEXT = "Просмотр комментария к отчету пока реализован как заглушка."

LEAD_TASK_PROPOSALS_LIST_TEXT = "Предложенные задачи:"
LEAD_TASK_PROPOSALS_EMPTY_TEXT = "Нет предложенных задач."
LEAD_TASK_PROPOSAL_NOT_FOUND_TEXT = "Предложение не найдено или уже обработано."
LEAD_TASK_PROPOSAL_ACCEPT_DEADLINE_PROMPT = "Выберите дедлайн для принятой задачи."
LEAD_TASK_PROPOSAL_ACCEPT_SUCCESS = "Задача принята и создана."
LEAD_TASK_PROPOSAL_REJECT_SUCCESS = "Предложение отклонено."

LEAD_TASKS_LIST_TEXT = "Ваши созданные задачи:"
LEAD_TASKS_EMPTY_TEXT = "У вас пока нет созданных задач."
LEAD_CREATE_TASK_TITLE_PROMPT = "Введите название задачи одним сообщением."
LEAD_CREATE_TASK_DESCRIPTION_PROMPT = (
    "Введите описание задачи одним сообщением.\n"
    "Если описание не нужно — отправьте '-'"
)
LEAD_CREATE_TASK_DEADLINE_PROMPT = "Выберите дедлайн в календаре."
LEAD_CREATE_TASK_SELECT_EMPLOYEE_PROMPT = "Выберите сотрудника или стажера."
LEAD_CREATE_TASK_NO_EMPLOYEES_TEXT = "Нет сотрудников или стажеров, прикрепленных к вам."
LEAD_CREATE_TASK_INVALID_EMPLOYEE_TEXT = "Используйте кнопки ниже."
LEAD_CREATE_TASK_SUCCESS = "Задача создана."
LEAD_CREATE_TASK_DEADLINE_SELECTED = "Дедлайн выбран: {deadline}"
LEAD_REPORTS_LIST_TEXT = "Список отчетов по вашим задачам:"
LEAD_REPORTS_EMPTY_TEXT = "По вашим задачам пока нет отчетов."
LEAD_VIEW_REPORT_SUCCESS = "Отчет по задаче '{task_title}'"
LEAD_CONFIRM_REPORT_SUCCESS = "Отчет по задаче '{task_title}' успешно принят."
LEAD_REPORT_NOT_FOUND_TEXT = "Отчет не найден."
LEAD_WEEKLY_SUCCESS = "Недельный отчет о сотруднике создан."
LEAD_REJECT_REPORT_PROMPT = "Введите комментарий к отклоненному отчету одним сообщением."
LEAD_REJECT_REPORT_SUCCESS = "Отчет успешно отправлен на доработку."
LEAD_REJECT_COMMENT_EMPTY = "Комментарий пустой. Введите комментарий еще раз."

EMPLOYEE_TASKS_LIST_TEXT = "Ваши назначенные задачи:"
EMPLOYEE_TASKS_EMPTY_TEXT = "У вас пока нет назначенных задач."
INTERN_TASKS_LIST_TEXT = "Ваши назначенные задачи:"
INTERN_TASKS_EMPTY_TEXT = "У вас пока нет назначенных задач."
TASK_ACCEPT_SUCCESS_TEXT = "Задача принята в работу."
TASK_FINISH_SUCCESS_TEXT = "Задача завершена."
TASK_STATUS_ALREADY_CHANGED_TEXT = "Статус задачи уже был изменён."
TASK_ACTION_NOT_ALLOWED_TEXT = "Это действие недоступно для этой задачи."
TASK_NOT_FOUND_TEXT = "Задача не найдена."

ACTION_CANCELLED_TEXT = "Действие отменено."

ROLE_REQUEST_CHOOSE_TEXT = "Выберите роль, которую хотите получить:"

NO_AVAILABLE_ROLES_TEXT = "У вас уже есть все доступные роли."

ROLE_REQUEST_SENT_TEXT = "Запрос на роль '{role}' отправлен"

START_WORK_REMINDER_TEXT = (
    "🔔 <b>Напоминание</b>\n\nПеред началом рабочего дня необходимо отметиться."
)

END_WORK_REMINDER_TEXT = (
    "🔔 <b>Напоминание</b>\n\nРабочий день завершается — не забудьте отметиться."
)

START_MENU_OPEN_TEXT = "Открываю стартовое меню."

SUPERUSER_ROLE_REQUESTS_LIST_TEXT = "Список запросов на роли:\n{requests}"
SUPERUSER_ROLE_REQUESTS_EMPTY_TEXT = "Нет активных запросов на роли."
SUPERUSER_CONFIRM_ROLE_PROMPT = "Введите Telegram ID и роль через пробел."
SUPERUSER_CONFIRM_ROLE_SUCCESS = "Роль {role} успешно выдана пользователю {tg_id}."
SUPERUSER_CONFIRM_ROLE_ERROR = "Запрос не найден."
SUPERUSER_CONFIRM_ROLE_FORMAT_ERROR = "Неверный формат. Ожидается: ID роль"

OFFER_TASK_TITLE_PROMPT = "Введите заголовок задачи одним сообщением."
OFFER_TASK_DESCRIPTION_PROMPT = "Опишите задачу одним сообщением."
OFFER_TASK_NO_MANAGERS_TEXT = "Не найдено прикрепленных руководителей."
OFFER_TASK_INVALID_MANAGER_TEXT = "Используйте кнопки ниже."
OFFER_TASK_SUCCESS_TEXT = "Задача отправлена вашим руководителям для подтверждения."

VISIT_START_SUCCESS_TEXT = "Начало рабочего дня зафиксировано."
VISIT_START_ALREADY_OPEN_TEXT = "У вас уже есть незавершённая запись рабочего дня."
VISIT_FINISH_SUCCESS_TEXT = "Конец рабочего дня зафиксирован."
VISIT_FINISH_NO_OPEN_TEXT = "Не найдена запись о начале рабочего дня."

EXIT_WITH_OPEN_VISIT_TEXT = (
    "Нельзя выйти из роли, пока рабочий день не завершён.\n"
    "Сначала нажмите «Завершить рабочий день»."
)

REPORT_TEXT_PROMPT = "Введите текст отчета одним сообщением."
REPORT_EMPTY_TEXT = "Текст отчета не должен быть пустым."
REPORT_SENT_TEXT = "Отчет отправлен. Статус задачи изменен на \"На рассмотрении\"."
LEAD_ACCEPT_REPORT_COMMENT_QUESTION = "Нужен комментарий к принятому отчету?"
LEAD_ACCEPT_REPORT_COMMENT_PROMPT = "Введите комментарий к отчету одним сообщением."
LEAD_ACCEPT_REPORT_SUCCESS = "Отчет принят."
LEAD_ACCEPT_REPORT_WITH_COMMENT_SUCCESS = "Отчет принят с комментарием."

LEAD_REJECT_REPORT_EMPLOYEE_NOTIFICATION = (
    "Отчет по задаче «{task_title}» отправлен на доработку.\n\n"
    "Комментарий руководителя:\n{comment}\n\n"
    "Задача снова доступна в списке задач."
)

SUPERUSER_REVOKE_ROLE_LIST_TEXT = "Список пользователей с ролями:"
SUPERUSER_REVOKE_ROLE_EMPTY_TEXT = "Нет пользователей с назначенными ролями."
SUPERUSER_REVOKE_ROLE_SUCCESS = "Роль {role} отозвана."
SUPERUSER_REVOKE_ROLE_NOT_FOUND = "У пользователя уже нет этой роли."
SUPERUSER_REVOKE_ROLE_LAST_SUPERUSER = "Нельзя отозвать роль у последнего администратора."

BIND_MANAGER_SELECT_TEXT = "Выберите руководителя, которому хотите отправить запрос."
BIND_MANAGER_NO_LEADS_TEXT = "Не найдено доступных руководителей."
BIND_MANAGER_INVALID_LEAD_TEXT = "Используйте кнопки ниже."
BIND_MANAGER_REQUEST_SENT_TEXT = "Запрос на привязку руководителя отправлен."
BIND_MANAGER_REQUEST_ALREADY_EXISTS_TEXT = "Такой запрос уже ожидает подтверждения."
BIND_MANAGER_ALREADY_BOUND_TEXT = "Вы уже закреплены за этим руководителем."

LEAD_BIND_REQUESTS = "Запросы на привязку"
LEAD_BIND_REQUESTS_EMPTY_TEXT = "Нет активных запросов на привязку."
LEAD_BIND_REQUEST_ACCEPTED_TEXT = "Запрос подтвержден. Пользователь {employee_label} закреплен за вами."
LEAD_BIND_REQUEST_REJECTED_TEXT = "Запрос отклонен."
LEAD_BIND_REQUEST_NOT_FOUND_TEXT = "Запрос не найден или уже обработан."

NOTIFICATION_SETTINGS_TEXT = (
    "Текущие настройки уведомлений:\n"
    "• начало дня: {morning_time}\n"
    "• конец дня: {evening_time}\n"
    "• часовой пояс: {timezone}\n\n"
    "Отправьте новые настройки одним сообщением в формате:\n"
    "<code>09:00 18:00 Europe/Moscow</code>\n\n"
    "Время указывается в формате HH:MM."
)
NOTIFICATION_SETTINGS_SUCCESS_TEXT = (
    "Настройки уведомлений сохранены:\n"
    "• начало дня: {morning_time}\n"
    "• конец дня: {evening_time}\n"
    "• часовой пояс: {timezone}"
)
NOTIFICATION_SETTINGS_FORMAT_ERROR_TEXT = (
    "Неверный формат. Отправьте настройки так:\n"
    "<code>09:00 18:00 Europe/Moscow</code>"
)
NOTIFICATION_SETTINGS_TIME_ERROR_TEXT = "Некорректное время. Используйте формат HH:MM, например 09:00."
NOTIFICATION_SETTINGS_TIMEZONE_ERROR_TEXT = "Некорректный часовой пояс. Пример: Europe/Moscow."

NOTIFICATION_SETTINGS_ORDER_ERROR_TEXT = (
    "Некорректный порядок времени. "
    "Время начала дня должно быть раньше времени окончания дня."
)