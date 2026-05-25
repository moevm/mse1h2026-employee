#!/bin/bash

set -e

cd /app

echo "[entrypoint] Инициализация таблиц Google Sheets"
python setup/init_tables.py

echo "[entrypoint] Cоздание суперпользователя"
python setup/init_superuser.py

echo "[entrypoint] Запуск бота"
cd /app/src
exec python main.py
