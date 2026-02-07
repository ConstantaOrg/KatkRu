#!/bin/bash

# Скрипт для валидации всей настройки перед запуском

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Валидация настройки Nginx + Security${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Функция для проверки
check() {
    local name="$1"
    local command="$2"
    local type="${3:-error}"  # error или warning
    
    echo -n "Проверка: $name... "
    
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        if [ "$type" == "error" ]; then
            echo -e "${RED}✗${NC}"
            ((ERRORS++))
        else
            echo -e "${YELLOW}⚠${NC}"
            ((WARNINGS++))
        fi
        return 1
    fi
}

echo -e "${YELLOW}=== 1. Проверка файлов ===${NC}\n"

check "nginx.conf существует" "test -f nginx.conf"
check "katkru_server.conf существует" "test -f katkru_server.conf"
check "Dockerfile_nginx существует" "test -f Dockerfile_nginx"
check "docker-compose.yml существует" "test -f docker-compose.yml"
check "docker-compose.security.yml существует" "test -f docker-compose.security.yml"
check "manage_bans.sh существует" "test -f scripts/manage_bans.sh"
check "auto_ban.sh существует" "test -f scripts/auto_ban.sh"
check "test_nginx_config.sh существует" "test -f scripts/test_nginx_config.sh"
check "Makefile существует" "test -f Makefile"

echo ""
echo -e "${YELLOW}=== 2. Проверка прав доступа ===${NC}\n"

check "manage_bans.sh исполняемый" "test -x scripts/manage_bans.sh" "warning"
check "auto_ban.sh исполняемый" "test -x scripts/auto_ban.sh" "warning"
check "test_nginx_config.sh исполняемый" "test -x scripts/test_nginx_config.sh" "warning"

if [ $WARNINGS -gt 0 ]; then
    echo -e "\n${YELLOW}Исправление прав доступа...${NC}"
    chmod +x scripts/*.sh 2>/dev/null
    echo -e "${GREEN}✓ Права исправлены${NC}"
fi

echo ""
echo -e "${YELLOW}=== 3. Проверка Docker ===${NC}\n"

check "Docker установлен" "command -v docker"
check "Docker Compose установлен" "command -v docker-compose"
check "Docker daemon запущен" "docker info"

echo ""
echo -e "${YELLOW}=== 4. Проверка синтаксиса конфигов ===${NC}\n"

# Проверка nginx конфига через Docker
if command -v docker > /dev/null 2>&1; then
    echo -n "Проверка синтаксиса nginx.conf... "
    if docker run --rm \
        -v "$(pwd)/nginx.conf:/tmp/nginx.conf:ro" \
        -v "$(pwd)/katkru_server.conf:/tmp/conf.d/katkru_server.conf:ro" \
        openresty/openresty:1.21.4.2-alpine \
        sh -c "mkdir -p /usr/local/openresty/nginx/conf/conf.d && \
               cp /tmp/nginx.conf /usr/local/openresty/nginx/conf/nginx.conf && \
               cp /tmp/conf.d/katkru_server.conf /usr/local/openresty/nginx/conf/conf.d/ && \
               nginx -t" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        echo -e "${RED}Ошибка в конфигурации nginx!${NC}"
        ((ERRORS++))
    fi
fi

# Проверка docker-compose конфига
echo -n "Проверка docker-compose.yml... "
if docker-compose config > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    ((ERRORS++))
fi

echo ""
echo -e "${YELLOW}=== 5. Проверка переменных окружения ===${NC}\n"

check ".env файл существует" "test -f .env" "warning"
check ".env.prod файл существует" "test -f .env.prod"

if [ -f .env ]; then
    check "REDIS_PASSWORD установлен" "grep -q 'REDIS_PASSWORD=' .env" "warning"
    check "ELASTIC_PASSWORD установлен" "grep -q 'ELASTIC_PASSWORD=' .env" "warning"
    check "PG_ADMIN_PASSWORD установлен" "grep -q 'PG_ADMIN_PASSWORD=' .env" "warning"
fi

echo ""
echo -e "${YELLOW}=== 6. Проверка портов ===${NC}\n"

check_port() {
    local port=$1
    local name=$2
    echo -n "Порт $port ($name) свободен... "
    if ! netstat -tuln 2>/dev/null | grep -q ":$port " && \
       ! ss -tuln 2>/dev/null | grep -q ":$port "; then
        echo -e "${GREEN}✓${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠ занят${NC}"
        ((WARNINGS++))
        return 1
    fi
}

if command -v netstat > /dev/null 2>&1 || command -v ss > /dev/null 2>&1; then
    check_port 80 "HTTP"
    check_port 443 "HTTPS"
    check_port 5432 "PostgreSQL"
    check_port 9200 "Elasticsearch"
    check_port 5601 "Kibana"
    check_port 3000 "Grafana"
else
    echo -e "${YELLOW}⚠ netstat/ss не найден, пропуск проверки портов${NC}"
fi

echo ""
echo -e "${YELLOW}=== 7. Проверка структуры директорий ===${NC}\n"

check "Директория logs существует" "test -d logs" "warning"
check "Директория scripts существует" "test -d scripts"
check "Директория docs существует" "test -d docs"

if [ ! -d logs ]; then
    echo -e "${YELLOW}Создание директории logs...${NC}"
    mkdir -p logs
    echo -e "${GREEN}✓ Создана${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Результаты валидации${NC}"
echo -e "${BLUE}========================================${NC}"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ Все проверки пройдены!${NC}"
    echo -e "\n${GREEN}Можно запускать:${NC}"
    echo -e "  ${BLUE}make build${NC}  - собрать образы"
    echo -e "  ${BLUE}make up${NC}     - запустить сервисы"
    echo -e "  ${BLUE}make test-nginx${NC} - протестировать конфигурацию"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Предупреждения: ${WARNINGS}${NC}"
    echo -e "\n${YELLOW}Можно запускать, но рекомендуется исправить предупреждения${NC}"
    exit 0
else
    echo -e "${RED}✗ Ошибки: ${ERRORS}${NC}"
    echo -e "${YELLOW}⚠ Предупреждения: ${WARNINGS}${NC}"
    echo -e "\n${RED}Необходимо исправить ошибки перед запуском!${NC}"
    exit 1
fi
