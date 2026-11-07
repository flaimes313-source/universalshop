from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database.connection import async_session_maker
from platforms.telegram.handlers import start, admin, catalog, cart, checkout, my_orders, timezone
from admin import products, orders, categories, settings, statistics, delivery


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with async_session_maker() as session:
            data["session"] = session
            return await handler(event, data)


async def start_bot():
    """
    Функция запуска бота.
    Bot и Dispatcher создаются ВНУТРИ этой функции, когда event loop уже работает.
    """
    print("🚀 Запуск Telegram-бота...")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(products.router)
    dp.include_router(orders.router)
    dp.include_router(categories.router)
    dp.include_router(settings.router)
    dp.include_router(statistics.router)
    dp.include_router(delivery.router)  # <-- Добавили
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(checkout.router)
    dp.include_router(my_orders.router)
    dp.include_router(timezone.router)

    await dp.start_polling(bot)