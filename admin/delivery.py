from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from decimal import Decimal
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from admin.states import DeliveryStates
from database.models import DeliveryMethod
from admin.menu import get_admin_main_menu

router = Router()

def get_delivery_admin_keyboard(methods: list[DeliveryMethod]) -> InlineKeyboardMarkup:
    keyboard = []
    for m in methods:
        status = "✅" if m.is_active else "❌"
        price_str = f"{m.price} ₽" if m.price else "Бесплатно"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status} {m.name} ({price_str})",
                callback_data=f"admin_del_view_{m.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="➕ Добавить способ", callback_data="admin_del_add")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_delivery_actions_keyboard(method_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Скрыть/Показать", callback_data=f"admin_del_toggle_{method_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_del_delete_{method_id}")],
        [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="admin_delivery")]
    ])

@router.callback_query(F.data == "admin_delivery")
async def list_delivery_methods(callback: types.CallbackQuery, session: AsyncSession):
    result = await session.execute(select(DeliveryMethod).order_by(DeliveryMethod.sort_order))
    methods = result.scalars().all()
    
    await callback.message.edit_text(
        "🚚 <b>Управление доставкой</b>\n\nВыберите способ для управления:",
        reply_markup=get_delivery_admin_keyboard(methods)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_del_view_"))
async def view_delivery_method(callback: types.CallbackQuery, session: AsyncSession):
    method_id = int(callback.data.split("_")[3])
    result = await session.execute(select(DeliveryMethod).where(DeliveryMethod.id == method_id))
    method = result.scalars().first()
    
    if not method:
        await callback.answer("Способ не найден", show_alert=True)
        return
        
    text = (
        f"🚚 <b>Способ доставки:</b> {method.name}\n"
        f"💰 Цена: {method.price} ₽\n"
        f"🏠 Требуется адрес: {'Да' if method.requires_address else 'Нет'}\n"
        f"🆓 Бесплатная: {'Да' if method.is_free else 'Нет'}\n"
        f"Статус: {'Активен' if method.is_active else 'Скрыт'}"
    )
    await callback.message.edit_text(text, reply_markup=get_delivery_actions_keyboard(method.id))
    await callback.answer()

@router.callback_query(F.data == "admin_del_add")
async def add_delivery_start(callback: types.CallbackQuery, state: FSMContext):
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
        await message.answer("❌ Ошибка. Введите число (например, 500 или 0):")
        return
    
    # Спрашиваем, нужен ли адрес
    await state.update_data(del_price=price)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да (курьер)", callback_data="del_requires_yes")],
        [InlineKeyboardButton(text="Нет (самовывоз)", callback_data="del_requires_no")],
    ])
    await message.answer("Требуется ли адрес для этого способа доставки?", reply_markup=keyboard)
    await state.set_state(DeliveryStates.waiting_for_requires_address)

@router.callback_query(DeliveryStates.waiting_for_requires_address, F.data.startswith("del_requires_"))
async def add_delivery_requires_address(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    requires = (callback.data == "del_requires_yes")
    data = await state.get_data()
    
    method = DeliveryMethod(
        name=data['del_name'],
        price=data['del_price'],
        requires_address=requires,
        is_free=(data['del_price'] == 0)
    )
    session.add(method)
    await session.commit()
    
    await callback.message.answer(f"✅ Способ доставки '{method.name}' добавлен.")
    await state.clear()
    
    # Возвращаемся к списку
    result = await session.execute(select(DeliveryMethod).order_by(DeliveryMethod.sort_order))
    methods = result.scalars().all()
    await callback.message.answer(
        "🚚 <b>Управление доставкой</b>\n\nВыберите способ для управления:",
        reply_markup=get_delivery_admin_keyboard(methods)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_del_toggle_"))
async def toggle_delivery_method(callback: types.CallbackQuery, session: AsyncSession):
    method_id = int(callback.data.split("_")[3])
    result = await session.execute(select(DeliveryMethod).where(DeliveryMethod.id == method_id))
    method = result.scalars().first()
    if method:
        method.is_active = not method.is_active
        await session.commit()
        await callback.answer("Статус изменен")
    result = await session.execute(select(DeliveryMethod).order_by(DeliveryMethod.sort_order))
    methods = result.scalars().all()
    await callback.message.edit_text(
        "🚚 <b>Управление доставкой</b>\n\nВыберите способ для управления:",
        reply_markup=get_delivery_admin_keyboard(methods)
    )

@router.callback_query(F.data.startswith("admin_del_delete_"))
async def delete_delivery_method(callback: types.CallbackQuery, session: AsyncSession):
    method_id = int(callback.data.split("_")[3])
    await session.execute(delete(DeliveryMethod).where(DeliveryMethod.id == method_id))
    await session.commit()
    await callback.answer("Способ доставки удален", show_alert=True)
    result = await session.execute(select(DeliveryMethod).order_by(DeliveryMethod.sort_order))
    methods = result.scalars().all()
    await callback.message.edit_text(
        "🚚 <b>Управление доставкой</b>\n\nВыберите способ для управления:",
        reply_markup=get_delivery_admin_keyboard(methods)
    )