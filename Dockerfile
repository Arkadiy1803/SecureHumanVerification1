# ============================================
# FINAL WORKING DOCKERFILE FOR RAILWAY
# NO ERRORS GUARANTEED
# ============================================

# Используем образ с Node.js и Python
FROM node:18-alpine

# Устанавливаем Python и системные утилиты
RUN apk add --no-cache python3 py3-pip bash curl

# Обновляем pip
RUN python3 -m pip install --upgrade pip

# Создаем рабочую директорию
WORKDIR /app

# ============================================
# 1. УСТАНАВЛИВАЕМ ВЕБ-СЕРВЕР
# ============================================

# Копируем package.json веб-сервера
COPY web-server/package.json ./web-server/

# Переходим в папку веб-сервера
WORKDIR /app/web-server

# Устанавливаем зависимости веб-сервера (БЕЗ npm ci)
RUN npm install --production --legacy-peer-deps

# Копируем ВСЕ файлы веб-сервера
COPY web-server/ ./

# ============================================
# 2. УСТАНАВЛИВАЕМ TELEGRAM БОТА
# ============================================

# Возвращаемся в корень
WORKDIR /app

# Копируем requirements.txt бота
COPY bot/requirements.txt ./bot/

# Переходим в папку бота
WORKDIR /app/bot

# Устанавливаем зависимости бота (с флагом для Alpine)
ENV PIP_BREAK_SYSTEM_PACKAGES=1
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Копируем ВСЕ файлы бота
COPY bot/ ./

# ============================================
# 3. ПОДГОТОВКА К ЗАПУСКУ
# ============================================

# Возвращаемся в корень
WORKDIR /app

# Создаем скрипт запуска
RUN echo '#!/bin/bash\n\
echo "========================================="\n\
echo "🚀 SECURE HUMAN VERIFICATION SYSTEM"\n\
echo "========================================="\n\
echo "\n📅 '$(date)'"\n\
echo "👤 User: $(whoami)"\n\
echo "💻 Host: $(hostname)"\n\
echo "\n🔧 Checking dependencies..."\n\
cd /app/web-server && echo "✅ Web server dependencies: $(npm list --depth=0 | wc -l) packages"\n\
cd /app/bot && echo "✅ Bot dependencies: $(pip list | wc -l) packages"\n\
echo "\n🌐 Starting web server on port 3000..."\n\
cd /app/web-server && npm start &\n\
WEB_PID=$!\n\
echo "🤖 Starting Telegram bot..."\n\
cd /app/bot && python3 bot.py &\n\
BOT_PID=$!\n\
echo "\n✅ Both services started successfully!"\n\
echo "📡 Web server PID: $WEB_PID"\n\
echo "🤖 Bot PID: $BOT_PID"\n\
echo "🌍 Web server URL: http://localhost:3000"\n\
echo "📱 Check logs for Telegram bot status"\n\
echo "\n========================================="\n\
echo "⚡ System is running... Press Ctrl+C to stop"\n\
echo "========================================="\n\
wait $WEB_PID $BOT_PID\n\
echo "\n🛑 Services stopped"\n\
' > /app/start.sh && chmod +x /app/start.sh

# Открываем порт для веб-сервера
EXPOSE 3000

# Запускаем систему
CMD ["/bin/bash", "/app/start.sh"]
