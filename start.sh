#!/bin/bash

# Скрипт запуска всей системы верификации

set -e

echo "🚀 Запуск системы верификации..."

# Цвета
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[+]${NC} $1"
}

print_error() {
    echo -e "${RED}[!]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[*]${NC} $1"
}

# Проверка наличия директорий
check_directories() {
    if [ ! -d "bot" ]; then
        print_error "Папка bot/ не найдена"
        exit 1
    fi
    
    if [ ! -d "web-server" ]; then
        print_error "Папка web-server/ не найдена"
        exit 1
    fi
    
    print_status "Структура проекта проверена"
}

# Запуск веб-сервера
start_web_server() {
    print_status "Запуск веб-сервера..."
    cd web-server
    
    # Проверка зависимостей
    if [ ! -d "node_modules" ]; then
        print_warning "Зависимости Node.js не установлены"
        print_warning "Запускаю: npm install"
        npm install
    fi
    
    # Запуск сервера в фоне
    npm start &
    WEB_PID=$!
    
    cd ..
    print_status "Веб-сервер запущен (PID: $WEB_PID)"
}

# Запуск Telegram бота
start_telegram_bot() {
    print_status "Запуск Telegram бота..."
    cd bot
    
    # Проверка виртуального окружения
    if [ ! -d "venv" ]; then
        print_error "Виртуальное окружение не найдено"
        print_warning "Создайте: python -m venv venv"
        exit 1
    fi
    
    # Активация venv и запуск бота
    source venv/bin/activate
    
    # Проверка зависимостей
    if ! python -c "import telegram" &> /dev/null; then
        print_warning "Зависимости Python не установлены"
        print_warning "Запускаю: pip install -r requirements.txt"
        pip install -r requirements.txt
    fi
    
    # Запуск бота в фоне
    python bot.py &
    BOT_PID=$!
    
    cd ..
    print_status "Telegram бот запущен (PID: $BOT_PID)"
}

# Проверка работы сервисов
check_services() {
    print_status "Проверка работы сервисов..."
    
    sleep 3
    
    # Проверка веб-сервера
    if curl -s http://localhost:3000 > /dev/null; then
        print_status "Веб-сервер работает: http://localhost:3000"
    else
        print_error "Веб-сервер не отвечает"
    fi
    
    # Информация для пользователя
    echo ""
    print_status "✅ Система запущена!"
    echo ""
    print_warning "Веб-сервер: http://localhost:3000"
    print_warning "Telegram бот: запущен"
    print_warning "Логи:"
    print_warning "  - Бот: tail -f bot/logs/verification_bot.log"
    print_warning "  - Сервер: tail -f web-server/logs/server.log"
    echo ""
    print_warning "Для остановки нажмите Ctrl+C"
}

# Обработка завершения
cleanup() {
    print_status "Остановка системы..."
    
    if [ ! -z "$WEB_PID" ]; then
        kill $WEB_PID 2>/dev/null || true
        print_status "Веб-сервер остановлен"
    fi
    
    if [ ! -z "$BOT_PID" ]; then
        kill $BOT_PID 2>/dev/null || true
        print_status "Telegram бот остановлен"
    fi
    
    exit 0
}

# Установка обработчика сигналов
trap cleanup INT TERM

# Основной процесс
main() {
    echo "========================================"
    echo "   Human Verification System           "
    echo "========================================"
    
    check_directories
    start_web_server
    start_telegram_bot
    check_services
    
    # Ожидание завершения
    wait
}

# Запуск
main
