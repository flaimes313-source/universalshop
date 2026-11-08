from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from database.models import Order, OrderItem, CartItem, Cart, Product
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
    delivery_method_name: str | None = None,
    bot: Bot | None = None
) -> Order:
    """Создает заказ на основе текущей корзины с проверкой остатков и списанием."""
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        raise ValueError("Пользователь не найден")

    # 1. Получаем корзину и её элементы с блокировкой строк товаров
    cart_result = await session.execute(
        select(Cart).where(Cart.user_id == user.id)
    )
    cart = cart_result.scalars().first()
    if not cart:
        raise ValueError("Корзина пуста")

    # Используем with_for_update() в select(), а не в selectinload
    items_result = await session.execute(
        select(CartItem)
        .where(CartItem.cart_id == cart.id)
        .options(selectinload(CartItem.product))
        .with_for_update()  # Блокировка строк
    )
    cart_items = items_result.scalars().all()
    if not cart_items:
        raise ValueError("Корзина пуста")

    # 2. Проверяем остатки и активность
    for item in cart_items:
        if not item.product or not item.product.is_active:
            raise ValueError(f"Товар '{item.product.name if item.product else 'Неизвестный'}' больше не доступен.")
        if item.quantity > item.product.stock:
            raise ValueError(f"Недостаточно товара '{item.product.name}'. Доступно: {item.product.stock}.")

    # 3. Считаем сумму
    total_amount = Decimal("0")
    for item in cart_items:
        total_amount += item.product.price * item.quantity
    total_amount += delivery_amount

    # 4. Создаем заказ
    order = Order(
        user_id=user.id,
        status="new",
        total_amount=total_amount,
        delivery_amount=delivery_amount,
        customer_name=customer_name,
        customer_phone=customer_phone,
        delivery_method_name=delivery_method_name,
        delivery_address=delivery_address,
        comment=comment
    )
    session.add(order)
    await session.flush()

    # 5. Переносим товары в заказ и списываем со склада
    order_items = []
    for item in cart_items:
        if not item.product:
            continue
        
        # Списываем остаток (атомарно)
        new_stock = item.product.stock - item.quantity
        if new_stock < 0:
            raise ValueError(f"Недостаточно товара '{item.product.name}'.")
        
        stmt = update(Product).where(Product.id == item.product_id).values(stock=new_stock)
        await session.execute(stmt)
        
        order_item = OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            product_name=item.product.name,
            price=item.product.price,
            quantity=item.quantity
        )
        session.add(order_item)
        order_items.append(order_item)

    # 6. Очищаем корзину
    for item in cart_items:
        await session.delete(item)

    await session.commit()

    # 7. Уведомляем админа
    if bot:
        await notify_admin_new_order(bot, order, order_items)

    return order