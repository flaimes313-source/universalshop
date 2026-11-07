from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from admin.states import SettingsStates
from database.models import ShopSetting
from admin.menu import get_admin_main_menu

router = Router()

SETTINGS_MAP = {
    "shop_name": {"name": "Название магазина", "type": "text"},
    "welcome_text": {"name": "Приветствие", "type": "text"},
    "contacts_text": {"name": "Контакты", "type": "text"},
    "currency": {"name": "Валюта (RUB, USD, EUR)", "type": "text"},
    "payment_manual_enabled": {"name": "Ручная оплата", "type": "toggle"},
    "payment_manual_details": {"name": "Реквизиты для ручной оплаты", "type": "text"},
}

def get_settings_keyboard(settings: dict) -> types.InlineKeyboardMarkup:
    keyboard = []
    for key, info in SETTINGS_MAP.items():
        if info["type"] == "toggle":
            current = settings.get(key, "0")
            status = "✅ Вкл" if current == "1" else "❌ Выкл"
            keyboard.append([
                types.InlineKeyboardButton(
                    text=f"{info['name']}: {status}",
                    callback_data=f"admin_setting_toggle_{key}"
                )
            ])
        else:
            keyboard.append([
                types.InlineKeyboardButton(
                    text=f"⚙️ {info['name']}",
                    callback_data=f"admin_setting_edit_{key}"
                )
            ])
    keyboard.append([types.InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="admin_back")])
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

async def _show_settings_text(session: AsyncSession) -> str:
    result = await session.execute(select(ShopSetting))
    settings = {s.key: s.value for s in result.scalars().all()}
    
    text = "<b>⚙️ Настройки магазина</b>\n\n"
    for key, info in SETTINGS_MAP.items():
        value = settings.get(key, "не задано")
        if info["type"] == "toggle":
            value = "Включено" if value == "1" else "Выключено"
        text += f"• <b>{info['name']}</b>: {value}\n"
    text += "\nВыберите настройку для изменения:"
    return text

@router.callback_query(F.data == "admin_settings")
async def show_settings(callback: types.CallbackQuery, session: AsyncSession):
    result = await session.execute(select(ShopSetting))
    settings = {s.key: s.value for s in result.scalars().all()}
    
    text = await _show_settings_text(session)
    await callback.message.edit_text(text, reply_markup=get_settings_keyboard(settings))
    await callback.answer()

# --- Переключатель (toggle) ---
@router.callback_query(F.data.startswith("admin_setting_toggle_"))
async def toggle_setting(callback: types.CallbackQuery, session: AsyncSession):
    key = callback.data.replace("admin_setting_toggle_", "")
    
    result = await session.execute(select(ShopSetting).where(ShopSetting.key == key))
    setting = result.scalars().first()
    
    if setting:
        setting.value = "0" if setting.value == "1" else "1"
    else:
        setting = ShopSetting(key=key, value="1")
        session.add(setting)
    
    await session.commit()
    await callback.answer("Настройка переключена")
    
    # Обновляем сообщение
    result = await session.execute(select(ShopSetting))
    settings = {s.key: s.value for s in result.scalars().all()}
    text = await _show_settings_text(session)
    await callback.message.edit_text(text, reply_markup=get_settings_keyboard(settings))

# --- Редактирование текста ---
@router.callback_query(F.data.startswith("admin_setting_edit_"))
async def edit_setting_start(callback: types.CallbackQuery, state: FSMContext):
    key = callback.data.replace("admin_setting_edit_", "")
    name = SETTINGS_MAP.get(key, {}).get("name", key)
    
    await state.update_data(setting_key=key)
    await callback.message.answer(f"Введите новое значение для <b>{name}</b>:")
    await state.set_state(SettingsStates.waiting_for_value)
    await callback.answer()

@router.message(SettingsStates.waiting_for_value)
async def save_setting(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    key = data.get('setting_key')
    
    if not key:
        await message.answer("❌ Ошибка: ключ настройки не найден.")
        await state.clear()
        return

    result = await session.execute(select(ShopSetting).where(ShopSetting.key == key))
    setting = result.scalars().first()
    
    if setting:
        setting.value = message.text
    else:
        new_setting = ShopSetting(key=key, value=message.text)
        session.add(new_setting)
    
    await session.commit()
    
    name = SETTINGS_MAP.get(key, {}).get("name", key)
    await message.answer(f"✅ Настройка <b>{name}</b> обновлена.")
    await state.clear()
    
    result = await session.execute(select(ShopSetting))
    settings = {s.key: s.value for s in result.scalars().all()}
    text = await _show_settings_text(session)
    await message.answer(text, reply_markup=get_settings_keyboard(settings))