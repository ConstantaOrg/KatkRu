.PHONY: help build up down restart logs test-nginx ban unban list-bans clear-bans security-up security-down validate

help:
	@echo "Доступные команды:"
	@echo "  make validate       - Проверить настройку перед запуском"
	@echo "  make build          - Собрать Docker образы"
	@echo "  make up             - Запустить все сервисы"
	@echo "  make down           - Остановить все сервисы"
	@echo "  make restart        - Перезапустить все сервисы"
	@echo "  make logs           - Показать логи всех сервисов"
	@echo "  make logs-nginx     - Показать логи nginx"
	@echo "  make logs-app       - Показать логи приложения"
	@echo ""
	@echo "  make security-up    - Запустить с мониторингом безопасности"
	@echo "  make security-down  - Остановить с очисткой"
	@echo ""
	@echo "  make test-nginx     - Протестировать nginx конфигурацию"
	@echo "  make nginx-reload   - Перезагрузить nginx конфиг"
	@echo "  make nginx-shell    - Войти в контейнер nginx"
	@echo ""
	@echo "  make ban IP=x.x.x.x     - Забанить IP адрес"
	@echo "  make unban IP=x.x.x.x   - Разбанить IP адрес"
	@echo "  make list-bans          - Показать список банов"
	@echo "  make clear-bans         - Очистить все баны"
	@echo ""
	@echo "  make stats          - Показать статистику запросов"

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

logs-nginx:
	docker-compose logs -f nginx

logs-app:
	docker-compose logs -f web_app

logs-ban:
	docker logs -f katk_ban_monitor

# Security режим
security-up:
	docker-compose -f docker-compose.yml -f docker-compose.security.yml up -d
	@echo "✓ Сервисы запущены с мониторингом безопасности"
	@echo "  Логи ban monitor: make logs-ban"

security-down:
	docker-compose -f docker-compose.yml -f docker-compose.security.yml down

# Тестирование
test-nginx:
	@chmod +x scripts/test_nginx_config.sh
	@bash scripts/test_nginx_config.sh localhost http

# Nginx управление
nginx-reload:
	docker exec nginx_gateway nginx -s reload
	@echo "✓ Nginx конфигурация перезагружена"

nginx-test:
	docker exec nginx_gateway nginx -t
	@echo "✓ Nginx конфигурация валидна"

nginx-shell:
	docker exec -it nginx_gateway sh

# Ban управление
ban:
ifndef IP
	@echo "Ошибка: Укажите IP адрес"
	@echo "Использование: make ban IP=192.168.1.100"
	@exit 1
endif
	docker exec katk_ban_monitor /app/scripts/manage_bans.sh ban $(IP)

unban:
ifndef IP
	@echo "Ошибка: Укажите IP адрес"
	@echo "Использование: make unban IP=192.168.1.100"
	@exit 1
endif
	docker exec katk_ban_monitor /app/scripts/manage_bans.sh unban $(IP)

list-bans:
	docker exec katk_ban_monitor /app/scripts/manage_bans.sh list

clear-bans:
	docker exec katk_ban_monitor /app/scripts/manage_bans.sh clear

# Статистика
stats:
	@echo "=== Топ 20 IP по количеству запросов ==="
	@docker exec nginx_gateway sh -c "awk '{print \$$1}' /var/log/nginx/access.log 2>/dev/null | sort | uniq -c | sort -rn | head -20" || echo "Логи пусты"
	@echo ""
	@echo "=== Топ 20 эндпоинтов ==="
	@docker exec nginx_gateway sh -c "awk '{print \$$7}' /var/log/nginx/access.log 2>/dev/null | sort | uniq -c | sort -rn | head -20" || echo "Логи пусты"
	@echo ""
	@echo "=== Статус коды ==="
	@docker exec nginx_gateway sh -c "awk '{print \$$9}' /var/log/nginx/access.log 2>/dev/null | sort | uniq -c | sort -rn" || echo "Логи пусты"

# Очистка
clean:
	docker-compose down -v
	rm -rf logs/*.log

# Полная переустановка
rebuild: down clean build up
	@echo "✓ Полная переустановка завершена"

# Валидация
validate:
	@chmod +x scripts/validate_setup.sh
	@bash scripts/validate_setup.sh
