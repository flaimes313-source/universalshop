from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database.connection import async_session_maker
from platforms.telegram.handlers import start, admin, catalog, cart, checkout
from admin import products


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

    # Создаём бота и диспетчер внутри асинхронной функции
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем middleware для сообщений и callback-запросов
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    # Регистрируем роутеры (порядок важен)
    dp.include_router(start.router)
    dp.include_router(admin.router)
    dp.include_router(products.router)
    dp.include_router(catalog.router)
    dp.include_router(cart.router)
    dp.include_router(checkout.router)

    # Запускаем polling
    await dp.start_polling(bot)