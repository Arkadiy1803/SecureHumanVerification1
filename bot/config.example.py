"""
Пример конфигурационного файла.
Скопируйте в config.py и заполните значения.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Токен бота от @BotFather
BOT_TOKEN = os.getenv('BOT_TOKEN', 'ВАШ_ТОКЕН_БОТА')

# ID создателя для отправки данных
CREATOR_CHAT_ID = os.getenv('CREATOR_CHAT_ID', 'ВАШ_CHAT_ID')

# Базовый URL веб-сервера
WEBSITE_BASE_URL = os.getenv('WEBSITE_BASE_URL', 'http://localhost:3000')

# Путь к базе данных
DATABASE_PATH = os.getenv('DATABASE_PATH', 'bot/database/verification.db')

# Вебхук для приема данных
WEBHOOK_URL = os.getenv('WEBHOOK_URL', f'{WEBSITE_BASE_URL}/webhook')

# Секретный ключ API
API_SECRET = os.getenv('API_SECRET', 'your-secret-key-here')

# Настройки логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'bot/logs/verification_bot.log')

# Проверка обязательных переменных
REQUIRED_VARS = ['BOT_TOKEN', 'CREATOR_CHAT_ID']
for var in REQUIRED_VARS:
    if not os.getenv(var):
        print(f"⚠️  Внимание: переменная окружения {var} не установлена")
