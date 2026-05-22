#!/bin/bash

set -e

cd "$(dirname "$0")/.."

echo "Проверка Python..."
if command -v python3 &>/dev/null; then
    echo "Python найден."
else
    echo "Ошибка: Python3 не найден."
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "Ошибка: .env не найден."
    exit 1
fi

echo "Настройка .venv..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate

echo "Установка зависимостей..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo "Инициализация таблиц Google Sheets..."
python3 setup/init_tables.py

echo "Проверка суперпользователя..."
python3 setup/init_superuser.py

echo "Установка завершена."
