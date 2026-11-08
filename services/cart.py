from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from decimal import Decimal
from database.models import Cart, CartItem, Product
from services.users import get_user_by_telegram_id

async def get_or_create_cart(session: AsyncSession, telegram_id: int) -> Cart:
    """Получает корзину пользователя или создает новую."""
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        raise ValueError("Пользователь не найден в БД. Сначала выполните /start.")

    result = await session.execute(
        select(Cart).where(Cart.user_id == user.id).options(selectinload(Cart.items))
    )
    cart = result.scalars().first()
    if not cart:
        cart = Cart(user_id=user.id)
        session.add(cart)
        await session.commit()
        result = await session.execute(
            select(Cart).where(Cart.id == cart.id).options(selectinload(Cart.items))
        )
        cart = result.scalars().first()
    return cart

async def add_to_cart(session: AsyncSession, telegram_id: int, product_id: int, quantity: int = 1):
    """Добавляет товар в корзину или увеличивает количество с проверкой остатков."""
    product_result = await session.execute(select(Product).where(Product.id == product_id))
    product = product_result.scalars().first()
    if not product:
        raise ValueError("Товар не найден.")
    if not product.is_active:
        raise ValueError("Товар скрыт и недоступен для покупки.")
    if product.stock < quantity:
        raise ValueError(f"Недостаточно товара на складе. Доступно: {product.stock}.")

    cart = await get_or_create_cart(session, telegram_id)
    
    result = await session.execute(
        select(CartItem)
        .where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
        .options(selectinload(CartItem.product))  # <-- ВАЖНО
    )
    item = result.scalars().first()
    
    if item:
        if item.quantity + quantity > product.stock:
            raise ValueError(f"Недостаточно товара. В корзине уже {item.quantity} шт., на складе {product.stock}.")
        item.quantity += quantity
    else:
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        session.add(item)
    
    await session.commit()

async def get_cart_items(session: AsyncSession, telegram_id: int) -> list[CartItem]:
    """Возвращает список товаров в корзине с данными о товаре."""
    cart = await get_or_create_cart(session, telegram_id)
    result = await session.execute(
        select(CartItem)
        .where(CartItem.cart_id == cart.id)
        .options(selectinload(CartItem.product))
    )
    return result.scalars().all()

async def update_quantity(session: AsyncSession, telegram_id: int, cart_item_id: int, delta: int):
    """Изменяет количество товара с проверкой принадлежности и остатков."""
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        raise ValueError("Пользователь не найден.")
    
    cart = await get_or_create_cart(session, telegram_id)
    
    result = await session.execute(
        select(CartItem)
        .where(CartItem.id == cart_item_id, CartItem.cart_id == cart.id)
        .options(selectinload(CartItem.product))  # <-- ВАЖНО
    )
    item = result.scalars().first()
    if not item:
        raise ValueError("Элемент не найден в вашей корзине.")

    if delta > 0:
        if item.quantity + delta > item.product.stock:
            raise ValueError(f"Недостаточно товара. Доступно: {item.product.stock}.")
    
    item.quantity += delta
    if item.quantity <= 0:
        await session.delete(item)
    await session.commit()

async def remove_item(session: AsyncSession, telegram_id: int, cart_item_id: int):
    """Удаляет товар из корзины с проверкой принадлежности."""
    user = await get_user_by_telegram_id(session, telegram_id)
    if not user:
        raise ValueError("Пользователь не найден.")
    
    cart = await get_or_create_cart(session, telegram_id)
    
    result = await session.execute(
        select(CartItem).where(CartItem.id == cart_item_id, CartItem.cart_id == cart.id)
    )
    item = result.scalars().first()
    if not item:
        raise ValueError("Элемент не найден в вашей корзине.")

    await session.delete(item)
    await session.commit()

async def clear_cart(session: AsyncSession, telegram_id: int):
    """Очищает корзину пользователя."""
    cart = await get_or_create_cart(session, telegram_id)
    await session.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
    await session.commit()

async def get_cart_total(session: AsyncSession, telegram_id: int) -> Decimal:
    """Считает итоговую сумму корзины (возвращает Decimal)."""
    items = await get_cart_items(session, telegram_id)
    total = Decimal("0")
    for item in items:
        if item.product:
            total += item.product.price * item.quantity
    return total