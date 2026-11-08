import asyncio
from sqlalchemy import select
from database.connection import engine, async_session_maker
from database.models import Base, ShopSetting, MenuItem

async def init_db():
    """Создает таблицы и заполняет базовые настройки при первом запуске."""
    print("⏳ Проверка и создание таблиц в базе данных...")
    
    # Создаем все таблицы, которых еще нет
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Таблицы созданы (или уже существовали).")

    # Проверяем и добавляем базовые настройки
    async with async_session_maker() as session:
        # 1. Настройки
        default_settings = [
            ("shop_name", "Мой Универсальный Магазин"),
            ("welcome_text", "Рады видеть вас в нашем магазине!"),
            ("contacts_text", "Свяжитесь с нами: @manager"),
            ("currency", "RUB"),
            ("payment_manual_enabled", "0"),
            ("payment_manual_details", "Реквизиты не указаны."),
            ("support_enabled", "1"),
            ("support_text", "Напишите ваш вопрос, и мы ответим вам в ближайшее время."),
        ]
        
        for key, value in default_settings:
            result = await session.execute(select(ShopSetting).where(ShopSetting.key == key))
            if not result.scalars().first():
                session.add(ShopSetting(key=key, value=value))
                print(f"  + Добавлена настройка: {key}")

        # 2. Меню
        default_menu = [
            ("Каталог", "catalog", 1),
            ("Корзина", "cart", 2),
            ("Мои заказы", "orders", 3),
            ("Контакты", "contacts", 4),
        ]
        
        for title, action, order in default_menu:
            result = await session.execute(select(MenuItem).where(MenuItem.title == title))
            if not result.scalars().first():
                session.add(MenuItem(title=title, action_type=action, sort_order=order))
                print(f"  + Добавлена кнопка меню: {title}")

        await session.commit()
        print("✅ Базовые настройки и меню проверены/добавлены.")

if __name__ == "__main__":
    asyncio.run(init_db())