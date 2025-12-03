#!/bin/bash
# start.sh - Скрипт запуска всей системы

echo "========================================"
echo "   Human Verification System           "
echo "========================================"

# Проверка Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js не установлен"
    echo "Установите Node.js с сайта: https://nodejs.org/"
    exit 1
fi

# Проверка npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm не установлен"
    echo "Установите npm вместе с Node.js"
    exit 1
fi

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    echo "Установите Python 3.8+"
    exit 1
fi

echo "✅ Проверка зависимостей пройдена"
echo "📦 Node.js: $(node --version)"
echo "🐍 Python: $(python3 --version)"

# Создаем необходимые директории
mkdir -p web-server/logs web-server/data bot/logs bot/database

# 1. Запускаем веб-сервер
echo ""
echo "🌐 Запуск веб-сервера..."
cd web-server

# Проверяем зависимости
if [ ! -d "node_modules" ]; then
    echo "📦 Устанавливаю зависимости Node.js..."
    npm install --silent
fi

echo "🚀 Веб-сервер запускается на http://localhost:3000"
npm start &
WEB_PID=$!
echo "📊 PID веб-сервера: $WEB_PID"

# 2. Запускаем Telegram бота
echo ""
echo "🤖 Запуск Telegram бота..."
cd ../bot

# Проверяем виртуальное окружение
if [ ! -d "venv" ]; then
    echo "🐍 Создаю виртуальное окружение Python..."
    python3 -m venv venv
fi

# Активируем venv
source venv/bin/activate

# Устанавливаем зависимости если нужно
if [ ! -f "venv/.deps_installed" ]; then
    echo "📦 Устанавливаю зависимости Python..."
    pip install -r requirements.txt --quiet
    touch venv/.deps_installed
fi

echo "🤖 Бот запускается..."
python bot.py &
BOT_PID=$!
echo "📊 PID бота: $BOT_PID"

echo ""
echo "========================================"
echo "✅ СИСТЕМА ЗАПУЩЕНА!"
echo "🌐 Веб-сервер: http://localhost:3000"
echo "🤖 Telegram бот: запущен"
echo ""
echo "📋 Команды для управления:"
echo "   CTRL+C - Остановить все сервисы"
echo "   kill $WEB_PID - Остановить веб-сервер"
echo "   kill $BOT_PID - Остановить бота"
echo "========================================"

# Ожидаем завершения
wait $WEB_PID $BOT_PID

echo ""
echo "🛑 Система остановлена"
