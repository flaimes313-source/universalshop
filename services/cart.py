from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from database.models import Cart, CartItem, Product

async def get_or_create_cart(session: AsyncSession, user_id: int) -> Cart:
    """Получает корзину пользователя или создает новую."""
    result = await session.execute(
        select(Cart).where(Cart.user_id == user_id).options(selectinload(Cart.items))
    )
    cart = result.scalars().first()
    if not cart:
        cart = Cart(user_id=user_id)
        session.add(cart)
        await session.commit()
        # Перезапрашиваем, чтобы загрузить связи
        result = await session.execute(
            select(Cart).where(Cart.id == cart.id).options(selectinload(Cart.items))
        )
        cart = result.scalars().first()
    return cart

async def add_to_cart(session: AsyncSession, user_id: int, product_id: int, quantity: int = 1):
    """Добавляет товар в корзину или увеличивает количество."""
    cart = await get_or_create_cart(session, user_id)
    
    # Ищем, есть ли уже этот товар в корзине
    result = await session.execute(
        select(CartItem).where(CartItem.cart_id == cart.id, CartItem.product_id == product_id)
    )
    item = result.scalars().first()
    
    if item:
        item.quantity += quantity
    else:
        item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
        session.add(item)
    
    await session.commit()

async def get_cart_items(session: AsyncSession, user_id: int) -> list[CartItem]:
    """Возвращает список товаров в корзине с данными о товаре."""
    cart = await get_or_create_cart(session, user_id)
    result = await session.execute(
        select(CartItem)
        .where(CartItem.cart_id == cart.id)
        .options(selectinload(CartItem.product)) # Загружаем данные товара
    )
    return result.scalars().all()

async def update_quantity(session: AsyncSession, cart_item_id: int, delta: int):
    """Изменяет количество товара (delta = +1 или -1)."""
    result = await session.execute(select(CartItem).where(CartItem.id == cart_item_id))
    item = result.scalars().first()
    if item:
        item.quantity += delta
        if item.quantity <= 0:
            await session.delete(item)
        await session.commit()

async def remove_item(session: AsyncSession, cart_item_id: int):
    """Удаляет товар из корзины."""
    await session.execute(delete(CartItem).where(CartItem.id == cart_item_id))
    await session.commit()

async def clear_cart(session: AsyncSession, user_id: int):
    """Очищает корзину пользователя."""
    cart = await get_or_create_cart(session, user_id)
    await session.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
    await session.commit()

async def get_cart_total(session: AsyncSession, user_id: int) -> float:
    """Считает итоговую сумму корзины."""
    items = await get_cart_items(session, user_id)
    total = sum(item.product.price * item.quantity for item in items if item.product)
    return float(total)