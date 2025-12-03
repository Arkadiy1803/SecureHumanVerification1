# Окончательный рабочий Dockerfile
FROM node:18-alpine AS web-builder

# Устанавливаем Python для бота
RUN apk add --no-cache python3 py3-pip bash

WORKDIR /app

# 1. Устанавливаем веб-сервер
COPY web-server/package.json ./web-server/
WORKDIR /app/web-server

# Используем npm install вместо npm ci
RUN npm install --omit=dev

# Копируем остальные файлы веб-сервера
COPY web-server/ ./

# 2. Возвращаемся к корню и устанавливаем бота
WORKDIR /app
COPY bot/requirements.txt ./bot/

WORKDIR /app/bot
# Разрешаем установку пакетов в системный Python для Alpine
ENV PIP_BREAK_SYSTEM_PACKAGES=1
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

# Копируем файлы бота
COPY bot/ ./

# 3. Создаем скрипт запуска
WORKDIR /app
RUN echo '#!/bin/sh\n\
echo "🚀 Starting Verification System..."\n\
echo "🌐 Starting web server on port 3000..."\n\
cd /app/web-server && npm start &\n\
echo "🤖 Starting Telegram bot..."\n\
cd /app/bot && python3 bot.py &\n\
echo "✅ Both services started"\n\
echo "📧 Web server: http://localhost:3000"\n\
wait' > start.sh && chmod +x start.sh

EXPOSE 3000

CMD ["/bin/sh", "/app/start.sh"]
