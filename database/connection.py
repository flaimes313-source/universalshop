from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import DATABASE_URL

# Создаем асинхронный движок
# echo=False отключает вывод всех SQL-запросов в консоль (для продакшена)
engine = create_async_engine(DATABASE_URL, echo=False)

# Фабрика сессий
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Функция-генератор для получения сессии в хендлерах
# Аннотация AsyncGenerator[AsyncSession, None] говорит, что мы возвращаем асинхронный генератор,
# который выдает объекты AsyncSession.
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session