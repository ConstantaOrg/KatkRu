#!/bin/bash

# Автоматический бан IP на основе анализа логов nginx
# Банит IP если:
# - Более 100 запросов за минуту
# - Более 10 ошибок 429 (rate limit) за минуту
# - Более 20 ошибок 401/403 за минуту

NGINX_LOG="/var/log/nginx/access.log"
BAN_SCRIPT="/app/scripts/manage_bans.sh"
TEMP_DIR="/tmp/nginx_ban_analysis"

# Пороги для бана
REQUESTS_THRESHOLD=100
RATE_LIMIT_THRESHOLD=10
AUTH_ERROR_THRESHOLD=20

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

mkdir -p $TEMP_DIR

echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] Запуск анализа логов nginx...${NC}"

# Анализ последней минуты логов
# BusyBox date не поддерживает -d, используем текущее время минус 1 минута
CURRENT_MINUTE=$(date '+%d/%b/%Y:%H:%M')
PREV_MINUTE=$(date -d '@'$(($(date +%s) - 60)) '+%d/%b/%Y:%H:%M' 2>/dev/null || date '+%d/%b/%Y:%H:%M')

# 1. Поиск IP с большим количеством запросов
echo -e "${YELLOW}Анализ частоты запросов...${NC}"
grep "$CURRENT_MINUTE\|$PREV_MINUTE" $NGINX_LOG 2>/dev/null | \
    awk '{print $1}' | \
    sort | uniq -c | sort -rn | \
    awk -v threshold=$REQUESTS_THRESHOLD '$1 > threshold {print $2, $1}' > $TEMP_DIR/high_frequency.txt

if [ -s $TEMP_DIR/high_frequency.txt ]; then
    while read ip count; do
        echo -e "${RED}IP $ip: $count запросов за минуту (порог: $REQUESTS_THRESHOLD)${NC}"
        $BAN_SCRIPT ban $ip
    done < $TEMP_DIR/high_frequency.txt
fi

# 2. Поиск IP с частыми 429 ошибками (rate limit)
echo -e "${YELLOW}Анализ ошибок rate limit (429)...${NC}"
grep "$CURRENT_MINUTE\|$PREV_MINUTE" $NGINX_LOG 2>/dev/null | \
    grep ' 429 ' | \
    awk '{print $1}' | \
    sort | uniq -c | sort -rn | \
    awk -v threshold=$RATE_LIMIT_THRESHOLD '$1 > threshold {print $2, $1}' > $TEMP_DIR/rate_limit_abuse.txt

if [ -s $TEMP_DIR/rate_limit_abuse.txt ]; then
    while read ip count; do
        echo -e "${RED}IP $ip: $count ошибок 429 за минуту (порог: $RATE_LIMIT_THRESHOLD)${NC}"
        $BAN_SCRIPT ban $ip
    done < $TEMP_DIR/rate_limit_abuse.txt
fi

# 3. Поиск IP с частыми ошибками авторизации (401/403)
echo -e "${YELLOW}Анализ ошибок авторизации (401/403)...${NC}"
grep "$CURRENT_MINUTE\|$PREV_MINUTE" $NGINX_LOG 2>/dev/null | \
    grep -E ' (401|403) ' | \
    awk '{print $1}' | \
    sort | uniq -c | sort -rn | \
    awk -v threshold=$AUTH_ERROR_THRESHOLD '$1 > threshold {print $2, $1}' > $TEMP_DIR/auth_abuse.txt

if [ -s $TEMP_DIR/auth_abuse.txt ]; then
    while read ip count; do
        echo -e "${RED}IP $ip: $count ошибок 401/403 за минуту (порог: $AUTH_ERROR_THRESHOLD)${NC}"
        $BAN_SCRIPT ban $ip
    done < $TEMP_DIR/auth_abuse.txt
fi

# 4. Поиск подозрительных User-Agent
echo -e "${YELLOW}Анализ подозрительных User-Agent...${NC}"
grep "$CURRENT_MINUTE\|$PREV_MINUTE" $NGINX_LOG 2>/dev/null | \
    grep -iE '(bot|crawler|spider|scraper|curl|wget|python|scanner)' | \
    grep -v -iE '(googlebot|bingbot|yandexbot)' | \
    awk '{print $1}' | \
    sort | uniq -c | sort -rn | \
    awk '$1 > 20 {print $2, $1}' > $TEMP_DIR/suspicious_ua.txt

if [ -s $TEMP_DIR/suspicious_ua.txt ]; then
    while read ip count; do
        echo -e "${YELLOW}IP $ip: $count запросов с подозрительным User-Agent${NC}"
        # Можно раскомментировать для автобана
         $BAN_SCRIPT ban $ip
    done < $TEMP_DIR/suspicious_ua.txt
fi

echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] Анализ завершен${NC}"

# Очистка временных файлов старше 1 дня
find $TEMP_DIR -type f -mtime +1 -delete

exit 0
