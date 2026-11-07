import os
from dotenv import load_dotenv

load_dotenv()

# --- Настройки Telegram ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# --- Настройки Базы Данных ---
DATABASE_URL = os.getenv("DATABASE_URL")
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", 30))

# --- Лицензия (защита от перепродажи) ---
LICENSE_KEY = os.getenv("LICENSE_KEY", "")
# Сюда впишите ключи, которые вы выдали клиентам (можно один для всех)
ALLOWED_LICENSE_KEYS = [
    "universalshop_demo_2026",  # <-- ЗАМЕНИТЕ НА СВОЙ КЛЮЧ
]

# Проверка, что критически важные переменные заданы
if not BOT_TOKEN:
    raise ValueError("❌ Не задан BOT_TOKEN в файле .env.")
if not ADMIN_ID:
    raise ValueError("❌ Не задан ADMIN_ID в файле .env.")
if not DATABASE_URL:
    raise ValueError("❌ Не задан DATABASE_URL в файле .env.")
if LICENSE_KEY not in ALLOWED_LICENSE_KEYS:
    raise ValueError("❌ Неверный или отсутствующий LICENSE_KEY. Обратитесь к разработчику.")