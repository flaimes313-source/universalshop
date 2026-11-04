from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import ShopSetting, MenuItem

async def get_setting(session: AsyncSession, key: str, default: str = "") -> str:
    """Получает значение настройки по ключу из БД."""
    result = await session.execute(select(ShopSetting).where(ShopSetting.key == key))
    setting = result.scalars().first()
    return setting.value if setting else default

async def get_menu_items(session: AsyncSession) -> list[MenuItem]:
    """Получает список активных кнопок главного меню, отсортированных по порядку."""
    result = await session.execute(
        select(MenuItem)
        .where(MenuItem.is_visible == True)
        .order_by(MenuItem.sort_order)
    )
    return list(result.scalars().all())