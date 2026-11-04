import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import engine, async_session_maker
from database.models import Base, ShopSetting, MenuItem

async def init_db():
    """Создает таблицы и заполняет базовые настройки при первом запуске."""
    print("⏳ Создание таблиц в базе данных...")
    
    # Создаем все таблицы, которых еще нет
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Таблицы созданы.")

    # Проверяем, есть ли базовые настройки, и если нет — создаем их
    async with async_session_maker() as session:
        # Проверка на наличие настроек
        from sqlalchemy import select
        result = await session.execute(select(ShopSetting).limit(1))
        if not result.scalars().first():
            print("⚙️ Заполнение базовых настроек...")
            default_settings = [
                ShopSetting(key="shop_name", value="Мой Универсальный Магазин"),
                ShopSetting(key="welcome_text", value="Рады видеть вас в нашем магазине!"),
                ShopSetting(key="contacts_text", value="Свяжитесь с нами: @manager"),
                ShopSetting(key="currency", value="RUB")
            ]
            session.add_all(default_settings)
            
            # Создаем базовое меню
            default_menu = [
                MenuItem(title="Каталог", action_type="catalog", sort_order=1),
                MenuItem(title="Корзина", action_type="cart", sort_order=2),
                MenuItem(title="Мои заказы", action_type="orders", sort_order=3),
                MenuItem(title="Контакты", action_type="contacts", sort_order=4),
            ]
            session.add_all(default_menu)
            
            await session.commit()
            print("✅ Настройки и меню по умолчанию добавлены.")

if __name__ == "__main__":
    asyncio.run(init_db())