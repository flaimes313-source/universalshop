from sqlalchemy.ext.asyncio import AsyncSession
from database.models import UserEvent
from services.users import get_user_by_telegram_id

async def log_event(
    session: AsyncSession,
    telegram_id: int,
    event_type: str,
    event_data: dict = None
):
    """Записывает событие пользователя в БД."""
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        return

    event = UserEvent(
        user_id=user.id,
        event_type=event_type,
        event_data=event_data
    )
    session.add(event)
    await session.commit()