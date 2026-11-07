from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.models import Order, OrderItem, CartItem, Cart
from services.users import get_user_by_telegram_id
from services.notifications import notify_admin_new_order
from decimal import Decimal
from aiogram import Bot

async def create_order(
    session: AsyncSession,
    telegram_id: int,
    customer_name: str,
    customer_phone: str,
    delivery_address: str | None,
    comment: str | None,
    delivery_amount: Decimal = Decimal("0"),
    bot: Bot | None = None
) -> Order:
    """Создает заказ на основе текущей корзины пользователя."""
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        raise ValueError("Пользователь не найден")

    # Получаем корзину и её элементы с загрузкой товаров
    cart_result = await session.execute(
        select(Cart).where(Cart.user_id == user.id)
    )
    cart = cart_result.scalars().first()
    if not cart:
        raise ValueError("Корзина пуста")

    items_result = await session.execute(
        select(CartItem)
        .where(CartItem.cart_id == cart.id)
        .options(selectinload(CartItem.product))
    )
    cart_items = items_result.scalars().all()
    if not cart_items:
        raise ValueError("Корзина пуста")

    # Считаем сумму товаров
    total_amount = Decimal("0")
    for item in cart_items:
        if item.product:
            total_amount += item.product.price * item.quantity
    total_amount += delivery_amount

    # Создаем заказ
    order = Order(
        user_id=user.id,
        status="new",
        total_amount=total_amount,
        delivery_amount=delivery_amount,
        customer_name=customer_name,
        customer_phone=customer_phone,
        delivery_address=delivery_address,
        comment=comment
    )
    session.add(order)
    await session.flush()  # Получаем ID заказа

    # Переносим товары из корзины в заказ
    order_items = []
    for item in cart_items:
        if not item.product:
            continue
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product.name,
            price=item.product.price,
            quantity=item.quantity
        )
        session.add(order_item)
        order_items.append(order_item)

    # Очищаем корзину
    for item in cart_items:
        await session.delete(item)

    await session.commit()

    # Отправляем уведомление админу
    if bot:
        await notify_admin_new_order(bot, order, order_items)

    return order