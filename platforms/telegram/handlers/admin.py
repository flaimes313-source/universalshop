from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from config import ADMIN_ID
from admin.menu import get_admin_main_menu

router = Router()

@router.message(Command("admin"))
async def cmd_admin(message: types.Message, session: AsyncSession):
    """Обработчик команды /admin. Проверяет права и открывает меню."""
    # Проверка, что пользователь — администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет доступа к панели администратора.")
        return

    # Если это админ, показываем меню
    await message.answer(
        text="<b>Панель управления</b>\n\nВыберите раздел для управления магазином:",
        reply_markup=get_admin_main_menu()
    )