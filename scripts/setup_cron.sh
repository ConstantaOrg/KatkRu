#!/bin/bash
# Скрипт для настройки cron в Docker контейнере

# Установка cron (если не установлен)
apt-get update && apt-get install -y cron

# Создание crontab задачи
echo "* * * * * cd /app && /usr/local/bin/python3 /app/scripts/monitor_resources.py >> /app/logs/cron.log 2>&1" > /etc/cron.d/resource-monitor

# Права на файл
chmod 0644 /etc/cron.d/resource-monitor

# Применение crontab
crontab /etc/cron.d/resource-monitor

# Запуск cron
service cron start

echo "✓ Cron настроен для мониторинга ресурсов (каждую минуту)"
