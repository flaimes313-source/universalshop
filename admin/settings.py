from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from admin.states import SettingsStates
from database.models import ShopSetting
from admin.menu import get_admin_main_menu

router = Router()

SETTINGS_MAP = {
    "shop_name": "Название магазина",
    "welcome_text": "Приветствие",
    "contacts_text": "Контакты",
    "currency": "Валюта (RUB, USD, EUR)",
    "payment_manual_enabled": "Ручная оплата (вкл/выкл)",
    "payment_manual_details": "Реквизиты для ручной оплаты",
}

def get_settings_keyboard() -> types.InlineKeyboardMarkup:
    keyboard = []
    for key, name in SETTINGS_MAP.items():
        keyboard.append([
            types.InlineKeyboardButton(
                text=f"⚙️ {name}",
                callback_data=f"admin_setting_edit_{key}"
            )
        ])
    keyboard.append([types.InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="admin_back")])
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

async def _show_settings_text(session: AsyncSession) -> str:
    result = await session.execute(select(ShopSetting))
    settings = {s.key: s.value for s in result.scalars().all()}
    
    text = "<b>⚙️ Настройки магазина</b>\n\n"
    for key, name in SETTINGS_MAP.items():
        value = settings.get(key, "не задано")
        text += f"• <b>{name}</b>: {value}\n"
    text += "\nВыберите настройку для изменения:"
    return text

@router.callback_query(F.data == "admin_settings")
async def show_settings(callback: types.CallbackQuery, session: AsyncSession):
    text = await _show_settings_text(session)
    await callback.message.edit_text(text, reply_markup=get_settings_keyboard())
    await callback.answer()

@router.callback_query(F.data.startswith("admin_setting_edit_"))
async def edit_setting_start(callback: types.CallbackQuery, state: FSMContext):
    key = callback.data.replace("admin_setting_edit_", "")
    name = SETTINGS_MAP.get(key, key)
    
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
    
    await message.answer(f"✅ Настройка <b>{SETTINGS_MAP.get(key, key)}</b> обновлена.")
    await state.clear()
    
    text = await _show_settings_text(session)
    await message.answer(text, reply_markup=get_settings_keyboard())