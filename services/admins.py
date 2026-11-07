from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import Admin
from config import ADMIN_ID

async def is_admin(session: AsyncSession, telegram_id: int) -> bool:
    """Проверяет, является ли пользователь администратором (владелец или менеджер)."""
    if telegram_id == ADMIN_ID:
        return True
    result = await session.execute(
        select(Admin).where(Admin.telegram_id == telegram_id, Admin.is_active == True)
    )
    admin = result.scalars().first()
    return admin is not None