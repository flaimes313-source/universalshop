from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from decimal import Decimal

from admin.states import DeliveryStates
from database.models import DeliveryMethod
from admin.menu import get_admin_main_menu

router = Router()

def get_delivery_admin_keyboard(methods: list[DeliveryMethod]) -> types.InlineKeyboardMarkup:
    """Клавиатура со списком способов доставки."""
    keyboard = []
    for m in methods:
        status = "✅" if m.is_active else "❌"
        keyboard.append([
            types.InlineKeyboardButton(
                text=f"{status} {m.name} ({m.price} ₽)",
                callback_data=f"admin_del_view_{m.id}"
            )
        ])
    keyboard.append([types.InlineKeyboardButton(text="➕ Добавить способ", callback_data="admin_del_add")])
    keyboard.append([types.InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="admin_back")])
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_delivery_actions_keyboard(method_id: int) -> types.InlineKeyboardMarkup:
    """Клавиатура действий с конкретным способом доставки."""
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔄 Скрыть/Показать", callback_data=f"admin_del_toggle_{method_id}")],
        [types.InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_del_delete_{method_id}")],
        [types.InlineKeyboardButton(text="🔙 Назад к списку", callback_data="admin_delivery")]
    ])

@router.callback_query(F.data == "admin_delivery")
async def list_delivery_methods(callback: types.CallbackQuery, session: AsyncSession):
    """Показывает список способов доставки."""
    result = await session.execute(select(DeliveryMethod).order_by(DeliveryMethod.sort_order))
    methods = result.scalars().all()
    
    await callback.message.edit_text(
        "🚚 <b>Управление доставкой</b>\n\nВыберите способ для управления:",
        reply_markup=get_delivery_admin_keyboard(methods)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_del_view_"))
async def view_delivery_method(callback: types.CallbackQuery, session: AsyncSession):
    """Показывает действия с конкретным способом."""
    method_id = int(callback.data.split("_")[3])
    result = await session.execute(select(DeliveryMethod).where(DeliveryMethod.id == method_id))
    method = result.scalars().first()
    
    if not method:
        await callback.answer("Способ не найден", show_alert=True)
        return
        
    text = (
        f"🚚 <b>Способ доставки:</b> {method.name}\n"
        f"💰 Цена: {method.price} ₽\n"
        f"Статус: {'Активен' if method.is_active else 'Скрыт'}"
    )
    await callback.message.edit_text(text, reply_markup=get_delivery_actions_keyboard(method.id))
    await callback.answer()

@router.callback_query(F.data == "admin_del_add")
async def add_delivery_start(callback: types.CallbackQuery, state: FSMContext):
    """Начинает добавление способа доставки."""
    await callback.message.answer("Введите название нового способа доставки (например, 'Курьер'):")
    await state.set_state(DeliveryStates.waiting_for_name)
    await callback.answer()

@router.message(DeliveryStates.waiting_for_name)
async def add_delivery_name(message: types.Message, state: FSMContext):
    await state.update_data(del_name=message.text)
    await message.answer("Введите стоимость доставки в рублях (например, 500 или 0 для бесплатной):")
    await state.set_state(DeliveryStates.waiting_for_price)

@router.message(DeliveryStates.waiting_for_price)
async def add_delivery_price(message: types.Message, state: FSMContext, session: AsyncSession):
    try:
        price = Decimal(message.text.replace(",", "."))
    except:
        await message.answer("❌ Ошибка. Введите число (например, 500):")
        return
        
    data = await state.get_data()
    method = DeliveryMethod(name=data['del_name'], price=price)
    session.add(method)
    await session.commit()
    
    await message.answer(f"✅ Способ доставки '{method.name}' добавлен.")
    await state.clear()
    
    # Возвращаемся к списку
    result = await session.execute(select(DeliveryMethod).order_by(DeliveryMethod.sort_order))
    methods = result.scalars().all()
    await message.answer(
        "🚚 <b>Управление доставкой</b>\n\nВыберите способ для управления:",
        reply_markup=get_delivery_admin_keyboard(methods)
    )

@router.callback_query(F.data.startswith("admin_del_toggle_"))
async def toggle_delivery_method(callback: types.CallbackQuery, session: AsyncSession):
    """Скрывает/показывает способ доставки."""
    method_id = int(callback.data.split("_")[3])
    result = await session.execute(select(DeliveryMethod).where(DeliveryMethod.id == method_id))
    method = result.scalars().first()
    
    if method:
        method.is_active = not method.is_active
        await session.commit()
        await callback.answer("Статус изменен")
        
    # Возвращаемся к списку
    result = await session.execute(select(DeliveryMethod).order_by(DeliveryMethod.sort_order))
    methods = result.scalars().all()
    await callback.message.edit_text(
        "🚚 <b>Управление доставкой</b>\n\nВыберите способ для управления:",
        reply_markup=get_delivery_admin_keyboard(methods)
    )

@router.callback_query(F.data.startswith("admin_del_delete_"))
async def delete_delivery_method(callback: types.CallbackQuery, session: AsyncSession):
    """Удаляет способ доставки."""
    method_id = int(callback.data.split("_")[3])
    await session.execute(delete(DeliveryMethod).where(DeliveryMethod.id == method_id))
    await session.commit()
    
    await callback.answer("Способ доставки удален", show_alert=True)
    
    # Возвращаемся к списку
    result = await session.execute(select(DeliveryMethod).order_by(DeliveryMethod.sort_order))
    methods = result.scalars().all()
    await callback.message.edit_text(
        "🚚 <b>Управление доставкой</b>\n\nВыберите способ для управления:",
        reply_markup=get_delivery_admin_keyboard(methods)
    )