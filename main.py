import asyncio
from datetime import datetime, timedelta
from sqlalchemy import delete

from config import LICENSE_KEY, ALLOWED_LICENSE_KEYS
from database.connection import async_session_maker
from database.models import UserEvent
from database.init_db import init_db
from database.updates.update_v1 import update_v1
from platforms.telegram.bot import start_bot


async def cleanup_old_events(days: int = 30):
    """Фоновая задача: раз в сутки удаляет события старше N дней."""
    while True:
        await asyncio.sleep(86400)
        cutoff = datetime.utcnow() - timedelta(days=days)
        async with async_session_maker() as session:
            await session.execute(delete(UserEvent).where(UserEvent.created_at < cutoff))
            await session.commit()
            print(f"🧹 Удалены события старше {days} дней (до {cutoff}).")


async def main():
    """Точка входа с проверкой лицензии, инициализацией БД, миграциями и запуском."""
    if LICENSE_KEY not in ALLOWED_LICENSE_KEYS:
        print("❌ Ошибка: неверный лицензионный ключ. Бот не запущен.")
        return

    # 1. Инициализация БД (создание таблиц, если их нет)
    await init_db()

    # 2. Применение миграций (добавление новых колонок в существующие таблицы)
    await update_v1()

    # 3. Запускаем фоновую задачу очистки
    asyncio.create_task(cleanup_old_events(30))

    # 4. Запускаем бота
    await start_bot()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен пользователем.")