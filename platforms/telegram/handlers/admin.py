from aiogram import Router, types, F
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from config import ADMIN_ID
from admin.menu import get_admin_main_menu
from services.admins import is_admin

router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: types.Message, session: AsyncSession):
    """Обработчик команды /admin."""
    if not await is_admin(session, message.from_user.id):
        await message.answer("⛔ У вас нет доступа к панели администратора.")
        return

    await message.answer(
        text="<b>Панель управления</b>\n\nВыберите раздел для управления магазином:",
        reply_markup=get_admin_main_menu()
    )


@router.message(F.text == "⚙️ Админ-панель")
async def admin_panel_button(message: types.Message, session: AsyncSession):
    """Обработчик кнопки 'Админ-панель' в главном меню."""
    if not await is_admin(session, message.from_user.id):
        await message.answer("⛔ У вас нет доступа.")
        return

    await message.answer(
        text="<b>Панель управления</b>\n\nВыберите раздел для управления магазином:",
        reply_markup=get_admin_main_menu()
    )