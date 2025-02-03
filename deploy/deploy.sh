#!/bin/bash

APP_DIR=$(pwd)
VENV_DIR="$APP_DIR/venv"
SERVICE_FILE="/etc/systemd/system/booru_scrapper.service"

# Установка виртуального окружения
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv $VENV_DIR
fi

source $VENV_DIR/bin/activate
pip install -r requirements.txt

# Создание файла сервиса systemd
bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=Scrapper Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=$APP_DIR
ExecStart=$VENV_DIR/bin/python -m run
ExecReload=$VENV_DIR/bin/python -m run
RestartSec=10
Restart=always
KillMode=process

[Install]
WantedBy=multi-user.target
[Unit]
Description=Scrapper Telegram Bot
After=network.target

EOF

# Перезагрузка systemd и запуск сервиса
systemctl daemon-reload
systemctl enable booru_scrapper.service
systemctl start booru_scrapper.service

echo "Бот успешно развернут и запущен с использованием systemd!"
