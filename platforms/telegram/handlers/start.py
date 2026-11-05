from aiogram import Router, types, F
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from services.settings import get_setting, get_menu_items
from services.users import get_or_create_user
from platforms.telegram.keyboards import get_main_menu_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession):
    """
    Обработчик команды /start.
    Создает пользователя в БД (если его нет) и отправляет приветствие с меню.
    """
    # 1. Создаем или получаем пользователя в БД
    user = await get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name
    )
    
    # 2. Получаем настройки из БД
    welcome_text = await get_setting(session, "welcome_text", "Добро пожаловать!")
    shop_name = await get_setting(session, "shop_name", "Наш магазин")
    
    # 3. Получаем кнопки меню из БД
    menu_items = await get_menu_items(session)
    
    # 4. Генерируем клавиатуру
    keyboard = get_main_menu_keyboard(menu_items)
    
    # 5. Формируем текст сообщения
    text = f"<b>{shop_name}</b>\n\n{welcome_text}"
    
    # 6. Отправляем сообщение
    await message.answer(text=text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: types.CallbackQuery, session: AsyncSession):
    """Возвращает пользователя в главное меню."""
    welcome_text = await get_setting(session, "welcome_text", "Добро пожаловать!")
    shop_name = await get_setting(session, "shop_name", "Наш магазин")
    menu_items = await get_menu_items(session)
    keyboard = get_main_menu_keyboard(menu_items)
    
    text = f"<b>{shop_name}</b>\n\n{welcome_text}"
    
    await callback.message.edit_text(text, reply_markup=None)
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()