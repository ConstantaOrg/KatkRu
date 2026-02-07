#!/bin/bash

# Скрипт нагрузочного тестирования для Nginx + API stack
# Тестирует: rate limiting, ban system, routing, cookies

set -e

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Настройки
TARGET_HOST="${1:-localhost}"
TARGET_PORT="${2:-80}"
BASE_URL="http://${TARGET_HOST}:${TARGET_PORT}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Нагрузочное тестирование Nginx Stack${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Target: ${CYAN}${BASE_URL}${NC}\n"

# Счетчики
TESTS_PASSED=0
TESTS_FAILED=0

# Функция для теста
test_request() {
    local name="$1"
    local url="$2"
    local expected_code="$3"
    local extra_args="${4:-}"
    
    echo -n "Тест: $name... "
    
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" $extra_args "$url")
    
    if [ "$response_code" == "$expected_code" ]; then
        echo -e "${GREEN}✓${NC} (HTTP $response_code)"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} (Ожидали $expected_code, получили $response_code)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Функция для массовых запросов
mass_requests() {
    local url="$1"
    local count="$2"
    local extra_args="${3:-}"
    
    local success=0
    local rate_limited=0
    local errors=0
    
    for i in $(seq 1 $count); do
        local code=$(curl -s -o /dev/null -w "%{http_code}" $extra_args "$url" 2>/dev/null)
        case $code in
            200|404) ((success++)) ;;
            429) ((rate_limited++)) ;;
            *) ((errors++)) ;;
        esac
    done
    
    echo "$success $rate_limited $errors"
}

echo -e "${YELLOW}=== 1. Базовые проверки доступности ===${NC}\n"

# Проверка что nginx работает (404 это нормально, главное что отвечает)
test_request "Nginx работает" "$BASE_URL/" "404"

# Проверка что nginx отвечает с правильным Server header
echo -n "Тест: Server header скрыт... "
server_header=$(curl -s -I "$BASE_URL/" | grep -i "^Server:" | awk '{print $2}')
if [ "$server_header" == "Katk" ]; then
    echo -e "${GREEN}✓${NC} (Server: $server_header)"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} (Server: $server_header)"
fi

echo ""
echo -e "${YELLOW}=== 2. Тестирование PUBLIC API ===${NC}\n"

# PUBLIC API должен быть доступен
test_request "PUBLIC API доступен" "$BASE_URL/api/v1/public/test" "404"

# Rate limiting на PUBLIC API
echo -n "Тест: Rate limiting на PUBLIC API (30 запросов)... "
result=$(mass_requests "$BASE_URL/api/v1/public/test" 30)
success=$(echo $result | awk '{print $1}')
rate_limited=$(echo $result | awk '{print $2}')
errors=$(echo $result | awk '{print $3}')

if [ $rate_limited -gt 0 ]; then
    echo -e "${GREEN}✓${NC} (Успешно: $success, Rate limited: $rate_limited, Ошибки: $errors)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} (Rate limiting не сработал! Все $success запросов прошли)"
    ((TESTS_FAILED++))
fi

echo ""
echo -e "${YELLOW}=== 3. Тестирование PRIVATE API ===${NC}\n"

# PRIVATE API без cookies - должен вернуть 401
test_request "PRIVATE API без cookies" "$BASE_URL/api/v1/private/test" "401"

# PRIVATE API с cookies - должен пройти (или 404 если эндпоинт не существует)
test_request "PRIVATE API с cookies" "$BASE_URL/api/v1/private/test" "404" \
    "-H 'Cookie: access_token=test123; refresh_token=test456'"

# Rate limiting на PRIVATE API с cookies
echo -n "Тест: Rate limiting на PRIVATE API (30 запросов с cookies)... "
result=$(mass_requests "$BASE_URL/api/v1/private/test" 30 \
    "-H 'Cookie: access_token=test123; refresh_token=test456'")
success=$(echo $result | awk '{print $1}')
rate_limited=$(echo $result | awk '{print $2}')
errors=$(echo $result | awk '{print $3}')

if [ $rate_limited -gt 0 ]; then
    echo -e "${GREEN}✓${NC} (Успешно: $success, Rate limited: $rate_limited, Ошибки: $errors)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} (Rate limiting не сработал! Все $success запросов прошли)"
    ((TESTS_FAILED++))
fi

echo ""
echo -e "${YELLOW}=== 4. Тестирование SERVER API ===${NC}\n"

# SERVER API снаружи - должен быть заблокирован
test_request "SERVER API заблокирован снаружи" "$BASE_URL/api/v1/server/test" "401"

echo ""
echo -e "${YELLOW}=== 5. Тестирование системы банов ===${NC}\n"

# Проверка что ban_monitor работает
if docker ps | grep -q katk_ban_monitor; then
    echo -e "${GREEN}✓${NC} Ban monitor контейнер запущен"
    ((TESTS_PASSED++))
    
    # Проверка iptables цепочки
    if docker exec katk_ban_monitor iptables -L KATK_BANLIST -n >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} iptables цепочка KATK_BANLIST существует"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗${NC} iptables цепочка KATK_BANLIST не найдена"
        ((TESTS_FAILED++))
    fi
    
    # Показать текущие баны
    echo -e "\n${CYAN}Текущие баны:${NC}"
    docker exec katk_ban_monitor /app/scripts/manage_bans.sh list 2>/dev/null || echo "Не удалось получить список банов"
else
    echo -e "${RED}✗${NC} Ban monitor контейнер не запущен"
    ((TESTS_FAILED++))
fi

echo ""
echo -e "${YELLOW}=== 6. Стресс-тест (100 запросов за 10 секунд) ===${NC}\n"

echo -n "Отправка 100 запросов... "
start_time=$(date +%s)
result=$(mass_requests "$BASE_URL/api/v1/public/test" 100)
end_time=$(date +%s)
duration=$((end_time - start_time))

success=$(echo $result | awk '{print $1}')
rate_limited=$(echo $result | awk '{print $2}')
errors=$(echo $result | awk '{print $3}')

echo -e "${GREEN}Завершено${NC}"
echo "  Время выполнения: ${duration}s"
echo "  Успешных запросов: $success"
echo "  Rate limited (429): $rate_limited"
echo "  Ошибок: $errors"
echo "  RPS: $((100 / duration))"

if [ $rate_limited -gt 50 ]; then
    echo -e "${GREEN}✓${NC} Rate limiting работает эффективно"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} Rate limiting пропустил слишком много запросов"
fi

echo ""
echo -e "${YELLOW}=== 7. Проверка логов nginx ===${NC}\n"

if [ -f "logs/access.log" ]; then
    echo -e "${GREEN}✓${NC} Access log существует"
    echo "  Последние 5 записей:"
    tail -5 logs/access.log | sed 's/^/    /'
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Access log не найден"
    ((TESTS_FAILED++))
fi

echo ""
echo -e "${YELLOW}=== 8. Анализ производительности ===${NC}\n"

# Средняя задержка
echo -n "Измерение средней задержки (10 запросов)... "
total_time=0
for i in $(seq 1 10); do
    time=$(curl -s -o /dev/null -w "%{time_total}" "$BASE_URL/api/v1/public/test" 2>/dev/null)
    total_time=$(echo "$total_time + $time" | bc)
done
avg_time=$(echo "scale=3; $total_time / 10" | bc)
echo -e "${GREEN}${avg_time}s${NC}"

if (( $(echo "$avg_time < 0.1" | bc -l) )); then
    echo -e "${GREEN}✓${NC} Отличная производительность (< 100ms)"
    ((TESTS_PASSED++))
elif (( $(echo "$avg_time < 0.5" | bc -l) )); then
    echo -e "${YELLOW}⚠${NC} Приемлемая производительность (< 500ms)"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗${NC} Медленная производительность (> 500ms)"
    ((TESTS_FAILED++))
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Результаты тестирования${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Пройдено: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Провалено: ${RED}${TESTS_FAILED}${NC}"
echo -e "Всего: $((TESTS_PASSED + TESTS_FAILED))"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}✓ Все тесты пройдены успешно!${NC}"
    exit 0
else
    echo -e "\n${RED}✗ Некоторые тесты провалились${NC}"
    exit 1
fi
