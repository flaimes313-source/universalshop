from aiogram import Router, types
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from services.settings import get_setting, get_menu_items
from platforms.telegram.keyboards import get_main_menu_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession):
    """
    Обработчик команды /start.
    Получает настройки из БД и отправляет приветствие с меню.
    """
    # 1. Получаем настройки из БД
    welcome_text = await get_setting(session, "welcome_text", "Добро пожаловать!")
    shop_name = await get_setting(session, "shop_name", "Наш магазин")
    
    # 2. Получаем кнопки меню из БД
    menu_items = await get_menu_items(session)
    
    # 3. Генерируем клавиатуру
    keyboard = get_main_menu_keyboard(menu_items)
    
    # 4. Формируем текст сообщения (жирным шрифтом название магазина)
    text = f"<b>{shop_name}</b>\n\n{welcome_text}"
    
    # 5. Отправляем сообщение
    await message.answer(text=text, reply_markup=keyboard, parse_mode="HTML")