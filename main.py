import asyncio
from platforms.telegram.bot import start_bot
from config import LICENSE_KEY, ALLOWED_LICENSE_KEYS

if __name__ == "__main__":
    # Проверка лицензии перед запуском
    if LICENSE_KEY not in ALLOWED_LICENSE_KEYS:
        print("❌ Ошибка: неверный лицензионный ключ. Бот не запущен.")
        exit(1)

    try:
        asyncio.run(start_bot())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен пользователем.")