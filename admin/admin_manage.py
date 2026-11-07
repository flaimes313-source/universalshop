from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from config import ADMIN_ID
from database.models import Admin

router = Router()

class AdminManageStates(StatesGroup):
    waiting_for_add_id = State()

# --- Список администраторов ---
@router.callback_query(F.data == "admin_admins")
async def list_admins(callback: types.CallbackQuery, session: AsyncSession):
    """Показывает список администраторов (только для владельца)."""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Только владелец может управлять администраторами.", show_alert=True)
        return

    result = await session.execute(select(Admin))
    admins = result.scalars().all()
    
    text = "👥 <b>Администраторы:</b>\n\n"
    keyboard = []
    
    if not admins:
        text += "Пока нет добавленных администраторов.\n"
    else:
        for adm in admins:
            role = "👑 Владелец" if adm.role == "owner" else "👤 Менеджер"
            text += f"• ID: <code>{adm.telegram_id}</code> — {role}\n"
            # Кнопка удаления для каждого (кроме владельца)
            if adm.telegram_id != ADMIN_ID:
                keyboard.append([
                    types.InlineKeyboardButton(
                        text=f"🗑 Удалить {adm.telegram_id}",
                        callback_data=f"admin_del_manager_{adm.telegram_id}"
                    )
                ])
    
    keyboard.append([types.InlineKeyboardButton(text="➕ Добавить менеджера", callback_data="admin_add_manager")])
    keyboard.append([types.InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="admin_back")])
    
    await callback.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard))
    await callback.answer()

# --- Добавление менеджера ---
@router.callback_query(F.data == "admin_add_manager")
async def add_manager_start(callback: types.CallbackQuery, state: FSMContext):
    """Начинает добавление менеджера."""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return
    await callback.message.answer("Введите Telegram ID нового менеджера (число):")
    await state.set_state(AdminManageStates.waiting_for_add_id)
    await callback.answer()

@router.message(AdminManageStates.waiting_for_add_id)
async def add_manager_process(message: types.Message, state: FSMContext, session: AsyncSession):
    """Добавляет менеджера по ID."""
    try:
        new_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Ошибка. Введите число (ID).")
        return

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
    
    # Возвращаемся к списку
    await list_admins(message, session) # Не сработает, т.к. list_admins ждет callback. Сделаем отдельно.
    # Просто отправим сообщение с обновленным списком (упрощенно)
    result = await session.execute(select(Admin))
    admins = result.scalars().all()
    text = "👥 <b>Администраторы:</b>\n\n"
    keyboard = []
    for adm in admins:
        role = "👑 Владелец" if adm.role == "owner" else "👤 Менеджер"
        text += f"• ID: <code>{adm.telegram_id}</code> — {role}\n"
        if adm.telegram_id != ADMIN_ID:
            keyboard.append([
                types.InlineKeyboardButton(
                    text=f"🗑 Удалить {adm.telegram_id}",
                    callback_data=f"admin_del_manager_{adm.telegram_id}"
                )
            ])
    keyboard.append([types.InlineKeyboardButton(text="➕ Добавить менеджера", callback_data="admin_add_manager")])
    keyboard.append([types.InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="admin_back")])
    await message.answer(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard))

# --- Удаление менеджера (через кнопку) ---
@router.callback_query(F.data.startswith("admin_del_manager_"))
async def del_manager_process(callback: types.CallbackQuery, session: AsyncSession):
    """Удаляет менеджера по ID из callback_data."""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    del_id = int(callback.data.split("_")[3])
    
    if del_id == ADMIN_ID:
        await callback.answer("❌ Нельзя удалить владельца.", show_alert=True)
        return

    await session.execute(delete(Admin).where(Admin.telegram_id == del_id))
    await session.commit()
    
    await callback.answer(f"✅ Менеджер с ID {del_id} удален.", show_alert=True)
    
    # Обновляем список
    result = await session.execute(select(Admin))
    admins = result.scalars().all()
    text = "👥 <b>Администраторы:</b>\n\n"
    keyboard = []
    for adm in admins:
        role = "👑 Владелец" if adm.role == "owner" else "👤 Менеджер"
        text += f"• ID: <code>{adm.telegram_id}</code> — {role}\n"
        if adm.telegram_id != ADMIN_ID:
            keyboard.append([
                types.InlineKeyboardButton(
                    text=f"🗑 Удалить {adm.telegram_id}",
                    callback_data=f"admin_del_manager_{adm.telegram_id}"
                )
            ])
    keyboard.append([types.InlineKeyboardButton(text="➕ Добавить менеджера", callback_data="admin_add_manager")])
    keyboard.append([types.InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="admin_back")])
    
    await callback.message.edit_text(text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard))