from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from config import ADMIN_ID
from database.models import Admin

router = Router()

class AdminManageStates(StatesGroup):
    waiting_for_id = State()

@router.callback_query(F.data == "admin_admins")
async def list_admins(callback: types.CallbackQuery, session: AsyncSession):
    """Показывает список администраторов (только для владельца)."""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Только владелец может управлять администраторами.", show_alert=True)
        return

    result = await session.execute(select(Admin))
    admins = result.scalars().all()
    
    text = "👥 <b>Администраторы:</b>\n\n"
    if not admins:
        text += "Пока нет добавленных администраторов.\n"
    else:
        for adm in admins:
            role = "👑 Владелец" if adm.role == "owner" else "👤 Менеджер"
            text += f"• ID: <code>{adm.telegram_id}</code> — {role}\n"
    
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="➕ Добавить менеджера", callback_data="admin_add_manager")],
        [types.InlineKeyboardButton(text="🗑 Удалить менеджера", callback_data="admin_del_manager")],
        [types.InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="admin_back")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "admin_add_manager")
async def add_manager_start(callback: types.CallbackQuery, state: FSMContext):
    """Начинает добавление менеджера."""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return
    await callback.message.answer("Введите Telegram ID нового менеджера (число):")
    await state.set_state(AdminManageStates.waiting_for_id)
    await callback.answer()

@router.message(AdminManageStates.waiting_for_id)
async def add_manager_process(message: types.Message, state: FSMContext, session: AsyncSession):
    """Добавляет менеджера по ID."""
    try:
        new_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Ошибка. Введите число (ID).")
        return

    # Проверяем, нет ли уже такого
    result = await session.execute(select(Admin).where(Admin.telegram_id == new_id))
    existing = result.scalars().first()
    if existing:
        await message.answer("❌ Этот пользователь уже администратор.")
        await state.clear()
        return

    new_admin = Admin(telegram_id=new_id, role="manager", added_by=message.from_user.id)
    session.add(new_admin)
    await session.commit()
    
    await message.answer(f"✅ Менеджер с ID {new_id} добавлен.")
    await state.clear()

@router.callback_query(F.data == "admin_del_manager")
async def del_manager_start(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Удаляет менеджера по ID."""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    await callback.message.answer("Введите Telegram ID менеджера для удаления:")
    await state.set_state(AdminManageStates.waiting_for_id)
    await state.update_data(action="delete")
    await callback.answer()

@router.message(AdminManageStates.waiting_for_id, F.text)
async def del_manager_process(message: types.Message, state: FSMContext, session: AsyncSession):
    """Удаляет менеджера."""
    data = await state.get_data()
    if data.get("action") != "delete":
        # Если это не удаление, то добавление (обработано выше)
        return

    try:
        del_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Ошибка. Введите число (ID).")
        return

    if del_id == ADMIN_ID:
        await message.answer("❌ Нельзя удалить владельца.")
        await state.clear()
        return

    await session.execute(delete(Admin).where(Admin.telegram_id == del_id))
    await session.commit()
    
    await message.answer(f"✅ Менеджер с ID {del_id} удален.")
    await state.clear()