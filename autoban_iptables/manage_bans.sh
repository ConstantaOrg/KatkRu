#!/bin/bash

# Скрипт для управления банами IP через iptables
# Использование:
#   ./manage_bans.sh ban <IP>           - забанить IP
#   ./manage_bans.sh unban <IP>         - разбанить IP
#   ./manage_bans.sh list               - показать список забаненных IP
#   ./manage_bans.sh clear              - очистить все баны
#   ./manage_bans.sh init               - инициализировать цепочку правил

CHAIN_NAME="KATK_BANLIST"
BAN_FILE="/var/log/nginx/banned_ips.txt"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Проверка прав root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Ошибка: Скрипт требует права root${NC}"
    exit 1
fi

# Инициализация цепочки правил
init_chain() {
    echo -e "${YELLOW}Инициализация цепочки правил iptables...${NC}"
    
    # Создаем цепочку если её нет
    if ! iptables -L $CHAIN_NAME -n >/dev/null 2>&1; then
        iptables -N $CHAIN_NAME
        echo -e "${GREEN}Цепочка $CHAIN_NAME создана${NC}"
    else
        echo -e "${YELLOW}Цепочка $CHAIN_NAME уже существует${NC}"
    fi
    
    # Добавляем правило для перенаправления в нашу цепочку (если его нет)
    if ! iptables -C INPUT -j $CHAIN_NAME 2>/dev/null; then
        iptables -I INPUT -j $CHAIN_NAME
        echo -e "${GREEN}Правило перенаправления добавлено${NC}"
    else
        echo -e "${YELLOW}Правило перенаправления уже существует${NC}"
    fi
    
    # Создаем файл для хранения списка банов
    touch $BAN_FILE
    echo -e "${GREEN}Инициализация завершена${NC}"
}

# Бан IP
ban_ip() {
    local IP=$1
    
    # Валидация IP
    if ! [[ $IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        echo -e "${RED}Ошибка: Неверный формат IP адреса${NC}"
        exit 1
    fi
    
    # Проверяем, не забанен ли уже
    if iptables -C $CHAIN_NAME -s $IP -j DROP 2>/dev/null; then
        echo -e "${YELLOW}IP $IP уже забанен${NC}"
        exit 0
    fi
    
    # Добавляем правило
    iptables -A $CHAIN_NAME -s $IP -j DROP
    
    # Сохраняем в файл
    echo "$IP $(date '+%Y-%m-%d %H:%M:%S')" >> $BAN_FILE
    
    echo -e "${GREEN}IP $IP успешно забанен${NC}"
}

# Разбан IP
unban_ip() {
    local IP=$1
    
    # Валидация IP
    if ! [[ $IP =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
        echo -e "${RED}Ошибка: Неверный формат IP адреса${NC}"
        exit 1
    fi
    
    # Удаляем правило
    if iptables -D $CHAIN_NAME -s $IP -j DROP 2>/dev/null; then
        # Удаляем из файла
        sed -i "/^$IP /d" $BAN_FILE
        echo -e "${GREEN}IP $IP успешно разбанен${NC}"
    else
        echo -e "${YELLOW}IP $IP не найден в списке банов${NC}"
    fi
}

# Список забаненных IP
list_bans() {
    echo -e "${YELLOW}Список забаненных IP:${NC}"
    echo "----------------------------------------"
    
    if [ -f $BAN_FILE ] && [ -s $BAN_FILE ]; then
        cat $BAN_FILE | while read line; do
            echo -e "${RED}$line${NC}"
        done
    else
        echo -e "${GREEN}Список банов пуст${NC}"
    fi
    
    echo "----------------------------------------"
    echo -e "${YELLOW}Активные правила iptables:${NC}"
    iptables -L $CHAIN_NAME -n -v --line-numbers 2>/dev/null || echo -e "${RED}Цепочка не инициализирована${NC}"
}

# Очистка всех банов
clear_bans() {
    echo -e "${YELLOW}Очистка всех банов...${NC}"
    
    # Очищаем цепочку
    if iptables -L $CHAIN_NAME -n >/dev/null 2>&1; then
        iptables -F $CHAIN_NAME
        echo -e "${GREEN}Цепочка $CHAIN_NAME очищена${NC}"
    fi
    
    # Очищаем файл
    > $BAN_FILE
    echo -e "${GREEN}Файл банов очищен${NC}"
}

# Главная логика
case "$1" in
    init)
        init_chain
        ;;
    ban)
        if [ -z "$2" ]; then
            echo -e "${RED}Ошибка: Укажите IP адрес${NC}"
            echo "Использование: $0 ban <IP>"
            exit 1
        fi
        init_chain
        ban_ip "$2"
        ;;
    unban)
        if [ -z "$2" ]; then
            echo -e "${RED}Ошибка: Укажите IP адрес${NC}"
            echo "Использование: $0 unban <IP>"
            exit 1
        fi
        unban_ip "$2"
        ;;
    list)
        list_bans
        ;;
    clear)
        read -p "Вы уверены, что хотите очистить все баны? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            clear_bans
        else
            echo -e "${YELLOW}Отменено${NC}"
        fi
        ;;
    *)
        echo "Использование: $0 {init|ban|unban|list|clear} [IP]"
        echo ""
        echo "Команды:"
        echo "  init          - Инициализировать цепочку правил iptables"
        echo "  ban <IP>      - Забанить IP адрес"
        echo "  unban <IP>    - Разбанить IP адрес"
        echo "  list          - Показать список забаненных IP"
        echo "  clear         - Очистить все баны"
        exit 1
        ;;
esac

exit 0
