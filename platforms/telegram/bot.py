from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from database.connection import async_session_maker
from platforms.telegram.handlers import start, admin # <-- добавили admin

# Middleware для передачи сессии БД в хендлеры
class DbSessionMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        async with async_session_maker() as session:
            data["session"] = session
            return await handler(event, data)

async def start_bot():
    """Функция запуска бота."""
    print("🚀 Запуск Telegram-бота...")

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем middleware
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    # Регистрируем роутеры
    dp.include_router(start.router)
    dp.include_router(admin.router) # <-- добавили admin

    await dp.start_polling(bot)