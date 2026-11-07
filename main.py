import asyncio
from datetime import datetime, timedelta
from sqlalchemy import delete

from config import LICENSE_KEY, ALLOWED_LICENSE_KEYS
from database.connection import async_session_maker
from database.models import UserEvent
from platforms.telegram.bot import start_bot


async def cleanup_old_events(days: int = 30):
    """
    Фоновая задача: раз в сутки удаляет события старше N дней.
    По умолчанию 30 дней.
    """
    while True:
        await asyncio.sleep(86400)  # Ждём 24 часа
        cutoff = datetime.utcnow() - timedelta(days=days)
        async with async_session_maker() as session:
            await session.execute(delete(UserEvent).where(UserEvent.created_at < cutoff))
            await session.commit()
            print(f"🧹 Удалены события старше {days} дней (до {cutoff}).")


async def main():
    """Точка входа с проверкой лицензии и запуском фоновой задачи."""
    # Проверка лицензии перед запуском
    if LICENSE_KEY not in ALLOWED_LICENSE_KEYS:
        print("❌ Ошибка: неверный лицензионный ключ. Бот не запущен.")
        return

    # Запускаем фоновую задачу очистки (она будет работать параллельно с ботом)
    asyncio.create_task(cleanup_old_events(30))

    # Запускаем бота
    await start_bot()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен пользователем.")