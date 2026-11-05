from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.models import Order, OrderItem
from services.users import get_user_by_telegram_id

router = Router()

@router.message(F.text == "Мои заказы")
async def show_my_orders(message: types.Message, session: AsyncSession):
    """Показывает список заказов пользователя."""
    # Находим пользователя в БД
    user = await get_user_by_telegram_id(session, message.from_user.id)
    if not user:
        await message.answer("Сначала выполните /start.")
        return

    # Получаем заказы пользователя с товарами
    result = await session.execute(
        select(Order)
        .where(Order.user_id == user.id)
        .options(selectinload(Order.items))
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()

    if not orders:
        await message.answer("📦 У вас пока нет заказов.")
        return

    # Формируем сообщение для каждого заказа
    for order in orders:
        text = (
            f"<b>Заказ #{order.id}</b>\n"
            f"📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📌 Статус: {order.status}\n"
            f"💰 Сумма: {order.total_amount} ₽\n\n"
            f"<b>Товары:</b>\n"
        )
        
        for item in order.items:
            text += f"• {item.product_name} — {item.quantity} шт. × {item.price} ₽\n"
        
        await message.answer(text)