from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

from services.cart import get_cart_items, get_cart_total
from services.orders import create_order
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
    """Клавиатура выбора способа доставки."""
    keyboard = []
    for method in delivery_methods:
        keyboard.append([InlineKeyboardButton(
            text=f"{method.name} ({method.price} ₽)",
            callback_data=f"delivery_{method.id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_order_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения заказа."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="order_confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="order_cancel")]
    ])


def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой пропуска."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏩ Пропустить")]],
        resize_keyboard=True
    )


@router.callback_query(F.data == "cart_checkout")
async def start_checkout(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Запускает процесс оформления заказа."""
    items = await get_cart_items(session, callback.from_user.id)
    if not items:
        await callback.answer("Корзина пуста!", show_alert=True)
        return

    await callback.message.answer(
        "📝 <b>Оформление заказа</b>\n\nШаг 1 из 5: Введите ваше имя:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CheckoutStates.waiting_for_name)
    await callback.answer()


@router.message(CheckoutStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(customer_name=message.text)
    await message.answer(
        "Шаг 2 из 5: Введите ваш номер телефона (например +79991234567):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CheckoutStates.waiting_for_phone)


@router.message(CheckoutStates.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext, session: AsyncSession):
    await state.update_data(customer_phone=message.text)
    
    # Получаем доступные способы доставки из БД
    result = await session.execute(select(DeliveryMethod).where(DeliveryMethod.is_active == True))
    delivery_methods = result.scalars().all()

    if not delivery_methods:
        # Если способов доставки нет, пропускаем этот шаг
        await state.update_data(delivery_id=None, delivery_address=None, delivery_amount=Decimal("0"))
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

    await state.update_data(delivery_id=delivery_id, delivery_amount=method.price)

    # Если это самовывоз (цена 0), адрес не нужен
    if method.price == 0:
        await state.update_data(delivery_address=None)
        await callback.message.answer(
            "Шаг 4 из 5: Введите комментарий к заказу (или нажмите 'Пропустить'):",
            reply_markup=get_skip_keyboard()
        )
        await state.set_state(CheckoutStates.waiting_for_comment)
    else:
        await callback.message.answer(
            "Шаг 4 из 5: Введите адрес доставки:",
            reply_markup=types.ReplyKeyboardRemove()
        )
        await state.set_state(CheckoutStates.waiting_for_address)

    await callback.answer()


@router.message(CheckoutStates.waiting_for_address)
async def process_address(message: types.Message, state: FSMContext):
    await state.update_data(delivery_address=message.text)
    await message.answer(
        "Шаг 5 из 5: Введите комментарий к заказу (или нажмите 'Пропустить'):",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(CheckoutStates.waiting_for_comment)


@router.message(CheckoutStates.waiting_for_comment)
async def process_comment(message: types.Message, state: FSMContext, session: AsyncSession):
    comment = None if message.text == "⏩ Пропустить" else message.text
    await state.update_data(comment=comment)

    data = await state.get_data()

    # Формируем итоговое сообщение для подтверждения
    items = await get_cart_items(session, message.from_user.id)
    total = await get_cart_total(session, message.from_user.id)
    delivery_amount = data.get('delivery_amount', Decimal("0"))
    final_total = Decimal(total) + delivery_amount

    text = (
        f"<b>Проверьте ваш заказ:</b>\n\n"
        f"👤 Имя: {data['customer_name']}\n"
        f"📞 Телефон: {data['customer_phone']}\n"
        f"🚚 Доставка: {data.get('delivery_address', 'Самовывоз')}\n"
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

    try:
        order = await create_order(
            session=session,
            telegram_id=callback.from_user.id,
            customer_name=data['customer_name'],
            customer_phone=data['customer_phone'],
            delivery_address=data.get('delivery_address'),
            comment=data.get('comment'),
            delivery_amount=data.get('delivery_amount', Decimal("0"))
        )

        await callback.message.edit_text(
            f"✅ Заказ #{order.id} успешно оформлен!\n\n"
            f"Мы свяжемся с вами для подтверждения."
        )
        await state.clear()
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка при оформлении заказа: {str(e)}")
        await state.clear()

    await callback.answer()


@router.callback_query(CheckoutStates.waiting_for_confirm, F.data == "order_cancel")
async def cancel_order(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Оформление заказа отменено.")
    await callback.answer()