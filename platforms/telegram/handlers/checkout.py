from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from services.cart import get_cart_items, get_cart_total
from services.orders import create_order
from services.settings import get_setting, get_menu_items
from services.analytics import log_event
from platforms.telegram.keyboards import get_main_menu_keyboard
from database.models import DeliveryMethod

router = Router()


class CheckoutStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_delivery = State()
    waiting_for_address = State()
    waiting_for_comment = State()
    waiting_for_confirm = State()


def get_delivery_keyboard(delivery_methods: list[DeliveryMethod]) -> InlineKeyboardMarkup:
    keyboard = []
    for method in delivery_methods:
        label = f"{method.name}"
        if method.price and method.price > 0:
            label += f" — {method.price} ₽"
        elif method.is_free:
            label += " — Бесплатно"
        keyboard.append([InlineKeyboardButton(
            text=label,
            callback_data=f"delivery_{method.id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_order_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="order_confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="order_cancel")]
    ])


def get_skip_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏩ Пропустить")]],
        resize_keyboard=True
    )


@router.callback_query(F.data == "cart_checkout")
async def start_checkout(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    items = await get_cart_items(session, callback.from_user.id)
    if not items:
        await callback.answer("Корзина пуста!", show_alert=True)
        return

    await log_event(session, callback.from_user.id, "checkout_start")

    await callback.message.answer(
        "📝 <b>Оформление заказа</b>\n\nШаг 1 из 5: Введите ваше имя:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CheckoutStates.waiting_for_name)
    await callback.answer()


@router.message(CheckoutStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(customer_name=message.text)
    await log_event(session, message.from_user.id, "checkout_step_name")
    await message.answer(
        "Шаг 2 из 5: Введите ваш номер телефона (например +79991234567):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CheckoutStates.waiting_for_phone)


@router.message(CheckoutStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(customer_phone=message.text)
    await log_event(session, message.from_user.id, "checkout_step_phone")
    
    result = await session.execute(select(DeliveryMethod).where(DeliveryMethod.is_active == True))
    delivery_methods = result.scalars().all()

    if not delivery_methods:
        await state.update_data(
            delivery_id=None, 
            delivery_address=None, 
            delivery_amount=Decimal("0"),
            delivery_method_name=None
        )
        await message.answer(
            "Шаг 4 из 5: Введите комментарий к заказу (или нажмите 'Пропустить'):",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CheckoutStates.waiting_for_comment)
        return

    await message.answer(
        "Шаг 3 из 5: Выберите способ доставки:",
        reply_markup=get_delivery_keyboard(delivery_methods)
    )
    await state.set_state(CheckoutStates.waiting_for_delivery)


@router.callback_query(CheckoutStates.waiting_for_delivery, F.data.startswith("delivery_"))
async def process_delivery(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    delivery_id = int(callback.data.split("_")[1])
    result = await session.execute(select(DeliveryMethod).where(DeliveryMethod.id == delivery_id))
    method = result.scalars().first()

    if not method:
        await callback.answer("Ошибка выбора доставки", show_alert=True)
        return

    # Цена теперь числовая
    price = method.price if method.price else Decimal("0")

    await state.update_data(
        delivery_id=delivery_id,
        delivery_method_name=method.name,
        delivery_amount=price,
        delivery_requires_address=method.requires_address  # запоминаем, нужен ли адрес
    )
    
    await log_event(session, callback.from_user.id, "checkout_step_delivery", {"delivery_id": delivery_id, "method_name": method.name})

    if method.requires_address:
        await callback.message.answer(
            "Шаг 4 из 5: Введите адрес доставки:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(CheckoutStates.waiting_for_address)
    else:
        await state.update_data(delivery_address=None)
        await callback.message.answer(
            "Шаг 4 из 5: Введите комментарий к заказу (или нажмите 'Пропустить'):",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CheckoutStates.waiting_for_comment)

    await callback.answer()


@router.message(CheckoutStates.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(delivery_address=message.text)
    await log_event(session, message.from_user.id, "checkout_step_address")
    await message.answer(
        "Шаг 5 из 5: Введите комментарий к заказу (или нажмите 'Пропустить'):",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(CheckoutStates.waiting_for_comment)


@router.message(CheckoutStates.waiting_for_comment)
async def process_comment(message: types.Message, state: FSMContext, session: AsyncSession):
    comment = None if message.text == "⏩ Пропустить" else message.text
    await state.update_data(comment=comment)
    await log_event(session, message.from_user.id, "checkout_step_comment")

    await message.answer("Сохраняю комментарий...", reply_markup=types.ReplyKeyboardRemove())

    data = await state.get_data()

    items = await get_cart_items(session, message.from_user.id)
    total = await get_cart_total(session, message.from_user.id)
    delivery_amount = data.get('delivery_amount', Decimal("0"))
    final_total = total + delivery_amount  # total уже Decimal

    text = (
        f"<b>Проверьте ваш заказ:</b>\n\n"
        f"👤 Имя: {data['customer_name']}\n"
        f"📞 Телефон: {data['customer_phone']}\n"
        f"🚚 Доставка: {data.get('delivery_method_name', 'Не выбрана')}\n"
        f"📍 Адрес: {data.get('delivery_address', 'Самовывоз')}\n"
        f"💬 Комментарий: {data.get('comment', 'Нет')}\n\n"
        f"<b>Товары:</b>\n"
    )
    for item in items:
        if item.product:
            text += f"- {item.product.name} x {item.quantity} шт. = {item.product.price * item.quantity} ₽\n"

    text += f"\n💰 Доставка: {delivery_amount} ₽\n"
    text += f"<b>Итого: {final_total} ₽</b>"

    await message.answer(text, reply_markup=get_confirm_order_keyboard())
    await state.set_state(CheckoutStates.waiting_for_confirm)


@router.callback_query(CheckoutStates.waiting_for_confirm, F.data == "order_confirm")
async def confirm_order(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()

    # Защита от повторного нажатия: проверяем, есть ли уже заказ в этом состоянии
    if data.get("order_created"):
        await callback.answer("Заказ уже создан.", show_alert=True)
        return
    await state.update_data(order_created=True)

    try:
        order = await create_order(
            session=session,
            telegram_id=callback.from_user.id,
            customer_name=data['customer_name'],
            customer_phone=data['customer_phone'],
            delivery_address=data.get('delivery_address'),
            comment=data.get('comment'),
            delivery_amount=data.get('delivery_amount', Decimal("0")),
            delivery_method_name=data.get('delivery_method_name'),
            bot=callback.bot
        )

        await log_event(session, callback.from_user.id, "order_created", {"order_id": order.id, "total": float(order.total_amount)})

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В главное меню", callback_data="main_menu")]
        ])
        
        text = (
            f"✅ Заказ #{order.id} успешно оформлен!\n\n"
            f"Мы свяжемся с вами для подтверждения."
        )
        
        payment_enabled = await get_setting(session, "payment_manual_enabled", "0")
        if payment_enabled == "1":
            details = await get_setting(session, "payment_manual_details", "Реквизиты не указаны.")
            text += f"\n\n💳 <b>Для оплаты переведите сумму на реквизиты:</b>\n{details}"

        await callback.message.edit_text(text, reply_markup=keyboard)
        await state.clear()
        
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при оформлении заказа: {str(e)}")
        await state.clear()

    await callback.answer()


@router.callback_query(CheckoutStates.waiting_for_confirm, F.data == "order_cancel")
async def cancel_order(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await log_event(session, callback.from_user.id, "checkout_abandon")
    await state.clear()
    
    await callback.message.answer("Возвращаемся в меню...", reply_markup=types.ReplyKeyboardRemove())
    await callback.message.edit_text("❌ Оформление заказа отменено.", reply_markup=None)

    welcome_text = await get_setting(session, "welcome_text", "Добро пожаловать!")
    shop_name = await get_setting(session, "shop_name", "Наш магазин")
    menu_items = await get_menu_items(session)
    from services.admins import is_admin
    admin_status = await is_admin(session, callback.from_user.id)
    keyboard = get_main_menu_keyboard(menu_items, admin_status)
    
    text = f"<b>{shop_name}</b>\n\n{welcome_text}"
    await callback.message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    
    await callback.answer()