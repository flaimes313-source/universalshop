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
async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session