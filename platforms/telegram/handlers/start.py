from aiogram import Router, types, F
from aiogram.filters import CommandStart
from sqlalchemy.ext.asyncio import AsyncSession

from services.settings import get_setting, get_menu_items
from services.users import get_or_create_user
from services.admins import is_admin
from platforms.telegram.keyboards import get_main_menu_keyboard
from config import ADMIN_ID

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message, session: AsyncSession):
    """Обработчик команды /start."""
    user = await get_or_create_user(
        session,
        telegram_id=message.from_user.id,
        full_name=message.from_user.full_name
    )
    
    welcome_text = await get_setting(session, "welcome_text", "Добро пожаловать!")
    shop_name = await get_setting(session, "shop_name", "Наш магазин")
    menu_items = await get_menu_items(session)
    
    admin_status = await is_admin(session, message.from_user.id)
    keyboard = get_main_menu_keyboard(menu_items, admin_status)
    
    text = f"<b>{shop_name}</b>\n\n{welcome_text}"
    await message.answer(text=text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: types.CallbackQuery, session: AsyncSession):
    """Возвращает пользователя в главное меню."""
    welcome_text = await get_setting(session, "welcome_text", "Добро пожаловать!")
    shop_name = await get_setting(session, "shop_name", "Наш магазин")
    menu_items = await get_menu_items(session)
    admin_status = await is_admin(session, callback.from_user.id)
    keyboard = get_main_menu_keyboard(menu_items, admin_status)
    
    text = f"<b>{shop_name}</b>\n\n{welcome_text}"
    
    await callback.message.edit_text(text, reply_markup=None)
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()