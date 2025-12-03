#!/usr/bin/env python3
"""
Проверка конфигурации бота
"""

import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 50)
print("ПРОВЕРКА КОНФИГУРАЦИИ БОТА")
print("=" * 50)

# Проверка токена
bot_token = os.getenv('BOT_TOKEN')
if bot_token:
    if bot_token == '7725874473:AAEEZj4LtuhjcL0lqN9nATOcihJr2uqyhi0':
        print("✅ Токен бота корректный")
    else:
        print(f"⚠️  Токен отличается от указанного")
    print(f"   Токен: {bot_token[:10]}...{bot_token[-10:]}")
else:
    print("❌ Токен бота не найден")

# Проверка Chat ID
chat_id = os.getenv('CREATOR_CHAT_ID')
if chat_id:
    if chat_id == '990561525':
        print("✅ Chat ID корректный")
    else:
        print(f"⚠️  Chat ID отличается")
    print(f"   Chat ID: {chat_id}")
else:
    print("❌ Chat ID не найден")

# Проверка MySQL конфигурации
db_config = [
    ('DB_HOST', 'gondola.proxy.rlwy.net'),
    ('DB_PORT', '15465'),
    ('DB_NAME', 'railway'),
    ('DB_USER', 'root')
]

print("\n🔧 Проверка MySQL конфигурации:")
for key, expected in db_config:
    value = os.getenv(key)
    if value:
        if value == expected:
            print(f"✅ {key}: {value}")
        else:
            print(f"⚠️  {key}: {value} (ожидалось: {expected})")
    else:
        print(f"❌ {key}: не найден")

print("\n" + "=" * 50)
