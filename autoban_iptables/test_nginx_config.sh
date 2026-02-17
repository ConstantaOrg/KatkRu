#!/bin/bash

# Скрипт для тестирования nginx конфигурации
# Проверяет все три типа роутов: public, private, server

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

HOST="${1:-localhost}"
PROTOCOL="${2:-http}"
BASE_URL="${PROTOCOL}://${HOST}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Тестирование Nginx конфигурации${NC}"
echo -e "${BLUE}Host: ${HOST}${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Счетчики
PASSED=0
FAILED=0

# Функция для теста
test_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="$3"
    local description="$4"
    local extra_args="${5:-}"
    
    echo -e "${YELLOW}Тест: ${name}${NC}"
    echo -e "  URL: ${url}"
    echo -e "  Ожидаемый статус: ${expected_status}"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" $extra_args "${url}")
    
    if [ "$response" == "$expected_status" ]; then
        echo -e "  ${GREEN}✓ PASSED${NC} (получен: ${response})"
        ((PASSED++))
    else
        echo -e "  ${RED}✗ FAILED${NC} (получен: ${response}, ожидался: ${expected_status})"
        ((FAILED++))
    fi
    echo -e "  ${description}\n"
}

echo -e "${BLUE}=== 1. PUBLIC API (доступен всем) ===${NC}\n"

test_endpoint \
    "Healthcheck" \
    "${BASE_URL}/api/v1/healthcheck" \
    "200" \
    "Базовый healthcheck эндпоинт"

test_endpoint \
    "Public Specialties" \
    "${BASE_URL}/api/v1/public/specialties" \
    "200" \
    "Публичный список специальностей"

test_endpoint \
    "Public Search" \
    "${BASE_URL}/api/v1/public/search/autocomplete?query=test" \
    "200" \
    "Публичный поиск (может вернуть 404 если эндпоинт не существует)"

echo -e "${BLUE}=== 2. PRIVATE API (требует cookies) ===${NC}\n"

test_endpoint \
    "Private без cookies" \
    "${BASE_URL}/api/v1/private/groups" \
    "401" \
    "Должен вернуть 401 без токенов"

test_endpoint \
    "Private с cookies" \
    "${BASE_URL}/api/v1/private/groups" \
    "401" \
    "С фейковыми токенами вернет 401 от приложения (не от nginx)" \
    "-b 'access_token=fake; refresh_token=fake'"

test_endpoint \
    "Private Teachers" \
    "${BASE_URL}/api/v1/private/teachers" \
    "401" \
    "Должен вернуть 401 без токенов"

test_endpoint \
    "Private Disciplines" \
    "${BASE_URL}/api/v1/private/disciplines" \
    "401" \
    "Должен вернуть 401 без токенов"

echo -e "${BLUE}=== 3. SERVER API (только whitelist) ===${NC}\n"

test_endpoint \
    "Server API снаружи" \
    "${BASE_URL}/api/v1/server/users/sign_up" \
    "403" \
    "Должен вернуть 403 для внешних запросов"

echo -e "${BLUE}=== 4. Rate Limiting ===${NC}\n"

echo -e "${YELLOW}Тест: Rate Limit${NC}"
echo -e "  Отправка 30 запросов подряд..."

rate_limit_429=0
for i in {1..30}; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/v1/public/specialties")
    if [ "$response" == "429" ]; then
        ((rate_limit_429++))
    fi
done

if [ $rate_limit_429 -gt 0 ]; then
    echo -e "  ${GREEN}✓ PASSED${NC} (получено ${rate_limit_429} ответов 429)"
    echo -e "  Rate limiting работает корректно\n"
    ((PASSED++))
else
    echo -e "  ${YELLOW}⚠ WARNING${NC} (не получено ответов 429)"
    echo -e "  Rate limiting может быть слишком мягким или не работает\n"
    ((FAILED++))
fi

echo -e "${BLUE}=== 5. Docs и OpenAPI ===${NC}\n"

test_endpoint \
    "API Docs" \
    "${BASE_URL}/api/docs" \
    "200" \
    "Swagger UI документация"

test_endpoint \
    "OpenAPI Schema" \
    "${BASE_URL}/api/openapi.json" \
    "200" \
    "OpenAPI спецификация"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Результаты тестирования${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Успешно: ${PASSED}${NC}"
echo -e "${RED}Провалено: ${FAILED}${NC}"
echo -e "${BLUE}========================================${NC}\n"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ Все тесты пройдены!${NC}\n"
    exit 0
else
    echo -e "${RED}✗ Некоторые тесты провалены${NC}\n"
    exit 1
fi
