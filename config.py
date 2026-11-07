import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# --- Настройки Telegram ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# --- Настройки Базы Данных ---
DATABASE_URL = os.getenv("DATABASE_URL")
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", 30))

# --- Лицензия (защита от перепродажи) ---
LICENSE_KEY = os.getenv("LICENSE_KEY", "")

# Сюда впишите ключи, которые вы выдали клиентам
ALLOWED_LICENSE_KEYS = [
    "universalshop_demo_2026",  # <-- ЗАМЕНИТЕ НА СВОЙ КЛЮЧ
]

# Привязка к токену бота (дополнительная защита)
# Если список пуст — проверка не выполняется
ALLOWED_BOT_TOKENS = [
    # "1234567890:AAH...",  # пример
]

# --- ПРОВЕРКИ ОБЯЗАТЕЛЬНЫХ ПЕРЕМЕННЫХ (без лицензии) ---

if not BOT_TOKEN:
    raise ValueError("❌ Не задан BOT_TOKEN в файле .env.")

if not ADMIN_ID:
    raise ValueError("❌ Не задан ADMIN_ID в файле .env.")

if not DATABASE_URL:
    raise ValueError("❌ Не задан DATABASE_URL в файле .env.")