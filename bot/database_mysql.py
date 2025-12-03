"""
MySQL database module for Verification Bot
"""

import mysql.connector
from mysql.connector import Error, pooling
import logging
from typing import Optional, Dict, Any
import json
from datetime import datetime
from config import DB_CONFIG

logger = logging.getLogger(__name__)

class MySQLDatabase:
    """Класс для работы с MySQL базой данных"""
    
    _instance = None
    _connection_pool = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MySQLDatabase, cls).__new__(cls)
            cls._instance._init_pool()
        return cls._instance
    
    def _init_pool(self):
        """Инициализация пула соединений"""
        try:
            self._connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name="verification_pool",
                pool_size=5,
                pool_reset_session=True,
                **DB_CONFIG
            )
            logger.info("Пул соединений MySQL инициализирован")
        except Error as e:
            logger.error(f"Ошибка создания пула соединений MySQL: {e}")
            self._connection_pool = None
    
    def get_connection(self):
        """Получение соединения из пула"""
        if self._connection_pool:
            try:
                return self._connection_pool.get_connection()
            except Error as e:
                logger.error(f"Ошибка получения соединения: {e}")
        return None
    
    def init_tables(self):
        """Инициализация таблиц в базе данных"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verification_users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_telegram_id (telegram_id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            # Таблица токенов верификации
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS verification_tokens (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    token VARCHAR(64) UNIQUE NOT NULL,
                    status ENUM('pending', 'completed', 'expired', 'failed') DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NULL,
                    completed_at TIMESTAMP NULL,
                    FOREIGN KEY (user_id) REFERENCES verification_users(id) ON DELETE CASCADE,
                    INDEX idx_token (token),
                    INDEX idx_status (status),
                    INDEX idx_expires (expires_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
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
                    region VARCHAR(100),
                    timezone VARCHAR(50),
                    browser_name VARCHAR(100),
                    browser_version VARCHAR(50),
                    os_name VARCHAR(100),
                    os_version VARCHAR(50),
                    platform VARCHAR(50),
                    is_mobile BOOLEAN,
                    screen_width INT,
                    screen_height INT,
                    language VARCHAR(10),
                    timezone_offset INT,
                    local_ips JSON,
                    geolocation JSON,
                    behavior_data JSON,
                    additional_data JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (token) REFERENCES verification_tokens(token) ON DELETE CASCADE,
                    INDEX idx_token (token),
                    INDEX idx_ip (ip_address),
                    INDEX idx_created (created_at)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            ''')
            
            connection.commit()
            logger.info("Таблицы MySQL успешно созданы/проверены")
            return True
            
        except Error as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    
    def save_verification_token(self, telegram_id: int, username: str, 
                               first_name: str, last_name: str, token: str) -> bool:
        """Сохранение токена верификации"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Добавить или обновить пользователя
            cursor.execute('''
                INSERT INTO verification_users (telegram_id, username, first_name, last_name)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                first_name = VALUES(first_name),
                last_name = VALUES(last_name),
                updated_at = CURRENT_TIMESTAMP
            ''', (telegram_id, username, first_name, last_name))
            
            user_id = cursor.lastrowid
            if user_id == 0:  # Если запись обновлена
                cursor.execute(
                    'SELECT id FROM verification_users WHERE telegram_id = %s',
                    (telegram_id,)
                )
                result = cursor.fetchone()
                user_id = result[0] if result else None
            
            if user_id:
                # Сохранить токен
                cursor.execute('''
                    INSERT INTO verification_tokens (user_id, token, expires_at)
                    VALUES (%s, %s, DATE_ADD(NOW(), INTERVAL 1 HOUR))
                ''', (user_id, token))
                
                connection.commit()
                logger.info(f"Токен сохранен для пользователя {telegram_id}")
                return True
            
            return False
            
        except Error as e:
            logger.error(f"Ошибка сохранения токена: {e}")
            return False
        finally:
            cursor.close()
            connection.close()
    
    def save_collected_data(self, token: str, collected_data: Dict[str, Any]) -> bool:
        """Сохранение собранных данных"""
        connection = self.get_connection()
        if not connection:
            return False
        
        try:
            cursor = connection.cursor()
            
            # Извлекаем данные
            geo = collected_data.get('geo', {})
            browser = collected_data.get('browser', {})
            device = collected_data.get('device', {})
            network = collected_data.get('network', {})
            behavior = collected_data.get('behavior', {})
            
            cursor.execute('''
                INSERT INTO collected_data (
                    token, ip_address, user_agent, country, city, region, timezone,
                    browser_name, browser_version, os_name, os_version, platform, is_mobile,
                    screen_width, screen_height, language, timezone_offset,
                    local_ips, geolocation, behavior_data, additional_data
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''', (
                token,
                collected_data.get('ip'),
                collected_data.get('user_agent'),
                geo.get('country'),
                geo.get('city'),
                geo.get('region'),
                geo.get('timezone'),
                browser.get('name'),
                browser.get('version'),
                device.get('os'),
                device.get('os_version'),
                device.get('platform'),
                device.get('is_mobile', False),
                device.get('screen_width'),
                device.get('screen_height'),
                collected_data.get('language'),
                collected_data.get('timezone_offset'),
                json.dumps(network.get('local_ips', [])),
                json.dumps(collected_data.get('geolocation', {})),
                json.dumps(behavior),
                json.dumps(collected_data.get('additional', {}))
            ))
            
            # Обновить статус токена
            cursor.execute('''
                UPDATE verification_tokens 
                SET status = 'completed', completed_at = NOW()
                WHERE token = %s AND status = 'pending'
            ''', (token,))
            
            connection.commit()
            logger.info(f"Данные сохранены для токена {token}")
            return True
            
        except Error as e:
            logger.error(f"Ошибка сохранения данных: {e}")
            return False
        finally:
            cursor.close()
            connection.close()

# Глобальный экземпляр базы данных
db = MySQLDatabase()

def init_database():
    """Инициализация базы данных"""
    return db.init_tables()

def save_verification_token(telegram_id: int, username: str, 
                           first_name: str, last_name: str, token: str) -> bool:
    """Сохранение токена верификации"""
    return db.save_verification_token(telegram_id, username, first_name, last_name, token)

def save_collected_data(token: str, collected_data: Dict[str, Any]) -> bool:
    """Сохранение собранных данных"""
    return db.save_collected_data(token, collected_data)

# Тестирование подключения
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    if init_database():
        print("✅ База данных инициализирована успешно")
        
        # Тестовое сохранение токена
        if save_verification_token(
            telegram_id=990561525,
            username='Arkadiy1803',
            first_name='Arkadiy',
            last_name='',
            token='test_token_123'
        ):
            print("✅ Тестовый токен сохранен")
        else:
            print("❌ Ошибка сохранения токена")
    else:
        print("❌ Ошибка инициализации базы данных")
