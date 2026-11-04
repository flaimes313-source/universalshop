import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# --- Настройки Telegram ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# --- Настройки Базы Данных ---
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "universalshop")

# Формируем строку подключения для SQLAlchemy (asyncpg)
DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Проверка, что критически важные переменные заданы
if not BOT_TOKEN:
    raise ValueError("❌ Не задан BOT_TOKEN в файле .env. Пожалуйста, откройте .env и вставьте токен из @BotFather.")
if not ADMIN_ID:
    raise ValueError("❌ Не задан ADMIN_ID в файле .env. Пожалуйста, укажите ваш Telegram ID.")