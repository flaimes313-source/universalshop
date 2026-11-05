import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env (локально)
# На сервере BotHost переменные берутся из системы
load_dotenv()

# --- Настройки Telegram ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# --- Настройки Базы Данных ---
# Используем готовую строку подключения из переменной окружения
# Формат: postgresql+asyncpg://user:password@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL")

# Таймаут подключения к БД в секундах
DB_CONNECT_TIMEOUT = int(os.getenv("DB_CONNECT_TIMEOUT", 30))

# Проверка, что критически важные переменные заданы
if not BOT_TOKEN:
    raise ValueError("❌ Не задан BOT_TOKEN в файле .env. Пожалуйста, откройте .env и вставьте токен из @BotFather.")
if not ADMIN_ID:
    raise ValueError("❌ Не задан ADMIN_ID в файле .env. Пожалуйста, укажите ваш Telegram ID.")
if not DATABASE_URL:
    raise ValueError("❌ Не задан DATABASE_URL в файле .env. Пожалуйста, укажите строку подключения к PostgreSQL.")