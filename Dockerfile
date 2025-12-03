FROM node:18-alpine AS web-builder

# Установка Python и зависимостей для бота
RUN apk add --no-cache python3 py3-pip

WORKDIR /app

# Копируем файлы веб-сервера
COPY web-server/package*.json ./web-server/
COPY web-server/server.js ./web-server/

# Устанавливаем зависимости веб-сервера
WORKDIR /app/web-server
RUN npm install --production

# Копируем файлы бота
WORKDIR /app
COPY bot/requirements.txt ./bot/
COPY bot/*.py ./bot/

# Устанавливаем зависимости бота
WORKDIR /app/bot
RUN pip3 install --no-cache-dir -r requirements.txt

# Возвращаемся в корень
WORKDIR /app

# Копируем остальные файлы
COPY . .

# Экспортируем порт
EXPOSE 3000

# Запускаем веб-сервер
CMD ["node", "web-server/server.js"]
