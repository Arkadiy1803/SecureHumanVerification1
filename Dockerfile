# Используем официальный Python образ с Node.js
FROM python:3.11-slim AS bot-builder

# Устанавливаем Node.js для веб-сервера
RUN apt-get update && apt-get install -y nodejs npm curl
RUN npm install -g npm@latest

# Создаем рабочую директорию
WORKDIR /app

# Копируем файлы бота
COPY bot/requirements.txt ./bot/
COPY bot/*.py ./bot/

# Устанавливаем зависимости бота в виртуальном окружении
WORKDIR /app/bot
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копируем файлы веб-сервера
WORKDIR /app
COPY web-server/package*.json ./web-server/
COPY web-server/server.js ./web-server/
COPY web-server/public ./web-server/public/

# Устанавливаем зависимости веб-сервера
WORKDIR /app/web-server
RUN npm ci --only=production

# Копируем остальные файлы
WORKDIR /app
COPY . .

# Настраиваем окружение для бота
WORKDIR /app/bot
ENV PYTHONPATH="/app/bot"
ENV PATH="/opt/venv/bin:$PATH"

# Создаем скрипт запуска
RUN echo '#!/bin/bash\n\
cd /app/web-server && npm start &\n\
cd /app/bot && /opt/venv/bin/python bot.py\n\
wait' > /app/start.sh && chmod +x /app/start.sh

# Экспортируем порт
EXPOSE 3000

# Запускаем оба сервиса
CMD ["/app/start.sh"]
