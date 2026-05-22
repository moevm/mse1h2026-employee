# MSE-employee

## Требования

- Python **3.11+**
- Аккаунт Google с доступом к Google Sheets API (при необходимости обратитесь к google_acc_readme.md за подробностями)
- Telegram Bot Token 

## Установка

Для установки вы можете воспользоваться скриптами из директории setup:
1. Для Linux и macOs: setup.sh
2. Для Windows: setup.bat

Или выполнить ручную установку

> Скрипты `setup/setup.sh` и `setup/setup.bat` также выполняют инициализацию структуры Google Sheets (создание листов и заголовков колонок) через `setup/init_tables.py`.
> Повторный запуск безопасен: скрипт не создает дубликаты листов и добавляет только отсутствующие заголовки.

### 1. Клонирование репозитория

```bash
git clone https://github.com/moevm/mse1h2026-employee.git
cd src
```

### 2. Создание виртуального окружения

```bash
python3 -m venv .venv
source .venv/bin/activate      # Linux / macOS
call .venv\Scripts\activate    # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

Если файл `requirements.txt` отсутствует, установите зависимости вручную:

```bash
pip install aiogram apscheduler gspread google-auth python-dotenv
```

### 4. Конфигурация проекта

Необходимо создать файл .env в корневой директории проекта. В нем задаются переменные окружения

#### Описание и примеры переменных окружения

| Переменная | Описание | Пример значения |
|---|---|---|
| `BOT_TOKEN` | Токен Telegram-бота | `123456789:ABCDEFGHIGKLMNOPQRSTUVWXYZ123456789` |
| `GOOGLE_CREDENTIALS_PATH` | Путь к JSON-ключу сервисного аккаунта | `credentials.json` |
| `GOOGLE_SHEET_ID` | ID Google Таблицы | `123456789ABCDEFGHIGKLMNOPQRSTUVWXYZabcdefghi` |
| `ROLES_SHEET_NAME` | Имя листа с ролями | `Роли` |
| `TASK_REQUESTS_SHEET_NAME` | Имя листа с запросами задач | `Запросы задач` |
| `TASKS_SHEET_NAME` | Имя листа с задачами | `Задачи` |
| `ROLE_REQUESTS_SHEET_NAME` | Имя листа с запросами ролей | `Запросы ролей` |
| `VISITS_SHEET_NAME` | Имя листа с посещениями | `Посещения` |
| `REMINDERS_TIMEZONE` | Часовой пояс для напоминаний | `Europe/Moscow` |
| `REMINDERS_DAYS_OF_WEEK` | Рабочие дни | `mon,tue,wed,thu,fri` |
| `REMINDER_MORNING_TIME` | Время утреннего напоминания | `08:50` |
| `REMINDER_EVENING_TIME` | Время вечернего напоминания | `16:50` |

## Запуск

Введите команды:
```bash
source .venv/bin/activate      # Linux / macOS
call .venv\Scripts\activate    # Windows
python ./srv/main.py
```

Теперь необходимо открыть бота в Telegram и отправить ему команду `/start`

## Структура таблиц

### Лист «Роли»

| TgID | Role | ManagerIDs |
|---|---|---|
| 1| lead | |
| 2 | employee | 1 |
| 3 | intern | 1 |
| 4 | superuser | |


### Лист «Задачи»

| TaskId | Title | Description | EmployeeID | AuthorID | Status | CreatedAt | UpdatedAt | Deadline |
|---|---|---|---|---|---|---|---|---|
| 1 | Задача 1 | Описание | 2 | 1 | created | 2024-01-01 09:00:00 | 2024-01-01 09:00:00 | 2024-01-31 |

## Роли пользователей

| Роль | Значение | Описание |
|---|---|---|
| `superuser` | суперпользователь | Управление запросами на роли, полный доступ |
| `lead` | руководитель | Управление задачами и отчетностью, исполнение роли сотрудника |
| `employee` | сотрудник | Работа с задачами, учёт посещаемости |
| `intern` | стажер | Базовый доступ, учёт посещаемости |

Один пользователь может иметь несколько ролей одновременно. Используемая роль выбирается при входе

## Добавление первого суперпользователя

Первого суперпользователя необходимо добавить вручную в лист **«Роли»**:

1. Узнать свой Telegram ID
2. Добавить строку в лист «Роли»:
   ```
   TgID: <ваш_id>
   Role: superuser
   ManagerIDs: (пусто)
   ```
3. Запустить бота и отправить ему команду `/start`
