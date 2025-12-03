#!/usr/bin/env python3
"""
Скрипт запуска Telegram бота
"""

import os
import sys
import logging
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging():
    """Настройка логирования"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/verification_bot.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_requirements():
    """Проверка зависимостей"""
    try:
        from telegram import __version__ as telegram_version
        print(f"✓ python-telegram-bot {telegram_version}")
        
        import dotenv
        print(f"✓ python-dotenv {dotenv.__version__}")
        
        import aiohttp
        print(f"✓ aiohttp {aiohttp.__version__}")
        
        return True
    except ImportError as e:
        print(f"✗ Отсутствует зависимость: {e}")
        print("Установите зависимости: pip install -r requirements.txt")
        return False

def main():
    """Основная функция запуска"""
    logger = setup_logging()
    
    print("=" * 50)
    print("Запуск Telegram Verification Bot")
    print("=" * 50)
    
    # Проверка зависимостей
    if not check_requirements():
        sys.exit(1)
    
    # Проверка токена бота
    if not os.path.exists('.env'):
        print("✗ Файл .env не найден")
        print("Создайте .env файл с токеном бота")
        sys.exit(1)
    
    # Загрузка переменных окружения
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('BOT_TOKEN'):
        print("✗ BOT_TOKEN не установлен в .env файле")
        sys.exit(1)
    
    # Запуск бота
    try:
        print("✓ Зависимости проверены")
        print("✓ Конфигурация загружена")
        print("🚀 Запуск бота...")
        
        from bot import main as run_bot
        run_bot()
        
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
