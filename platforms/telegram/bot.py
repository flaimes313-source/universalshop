from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database.connection import async_session_maker
from platforms.telegram.handlers import start, admin, catalog, cart, checkout, my_orders, timezone, support
from admin import (
    products, orders, categories, settings, statistics,
    delivery, customers, admin_manage, analytics, products_manage
)


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with async_session_maker() as session:
            data["session"] = session
            return await handler(event, data)


async def start_bot():
    print("🚀 Запуск Telegram-бота...")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    # Регистрируем роутеры (порядок важен)
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(support.router)
    dp.include_router(products.router)
    dp.include_router(products_manage.router)
    dp.include_router(orders.router)
    dp.include_router(categories.router)
    dp.include_router(settings.router)
    dp.include_router(statistics.router)
    dp.include_router(analytics.router)
    dp.include_router(delivery.router)
    dp.include_router(customers.router)
    dp.include_router(admin_manage.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(checkout.router)
    dp.include_router(my_orders.router)
    dp.include_router(timezone.router)

    await dp.start_polling(bot)