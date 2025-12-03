"""
Конфигурационный файл бота
Замените значения на реальные
"""

import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv('bot/.env')

# Токен бота от @BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN', 'ВАШ_ТОКЕН_БОТА')

# ID создателя для отправки данных
CREATOR_CHAT_ID = os.getenv('CREATOR_CHAT_ID', 'ВАШ_CHAT_ID')

# Базовый URL веб-сервера
WEBSITE_BASE_URL = os.getenv('WEBSITE_BASE_URL', 'https://your-domain.com')

# Настройки базы данных
DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot/database/verification.db')

# Настройки веб-сервера для приема данных
WEBHOOK_URL = os.getenv('WEBHOOK_URL', f'{WEBSITE_BASE_URL}/webhook')

# Секретный ключ для проверки запросов
API_SECRET = os.getenv('API_SECRET', 'your-secret-key-here')

# Настройки логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'bot/verification_bot.log')

# Проверка обязательных переменных
REQUIRED_VARS = ['BOT_TOKEN', 'CREATOR_CHAT_ID']
for var in REQUIRED_VARS:
    if not os.getenv(var):
        print(f"⚠️ Внимание: переменная окружения {var} не установлена")
