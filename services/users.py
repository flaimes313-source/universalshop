from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User, PlatformAccount

async def get_or_create_user(session: AsyncSession, telegram_id: int, full_name: str) -> User:
    """Получает пользователя по Telegram ID или создает нового."""
    # Ищем пользователя по привязанному аккаунту Telegram
    result = await session.execute(
        select(User)
        .join(PlatformAccount)
        .where(
            PlatformAccount.platform == "telegram",
            PlatformAccount.platform_id == str(telegram_id)
        )
    )
    user = result.scalars().first()
    
    if not user:
        # Если пользователя нет, создаем его
        user = User(full_name=full_name)
        session.add(user)
        await session.flush() # Получаем ID пользователя
        
        # Привязываем к нему аккаунт Telegram
        platform_account = PlatformAccount(
            user_id=user.id,
            platform="telegram",
            platform_id=str(telegram_id)
        )
        session.add(platform_account)
        await session.commit()
    
    return user

async def get_user_by_telegram_id(session: AsyncSession, telegram_id: int) -> User | None:
    """Просто получает пользователя по Telegram ID."""
    result = await session.execute(
        select(User)
        .join(PlatformAccount)
        .where(
            PlatformAccount.platform == "telegram",
            PlatformAccount.platform_id == str(telegram_id)
        )
    )
    return result.scalars().first()