from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.models import Product, ProductImage
from services.cart import add_to_cart

router = Router()

@router.message(F.text == "Каталог")
async def show_catalog(message: types.Message, session: AsyncSession):
    """Показывает каталог: список товаров с кнопкой 'В корзину'."""
    
    result = await session.execute(select(Product).where(Product.is_active == True))
    products = result.scalars().all()
    
    if not products:
        await message.answer("😔 В каталоге пока нет товаров.")
        return
    
    for product in products:
        # Получаем фото товара
        img_result = await session.execute(
            select(ProductImage).where(ProductImage.product_id == product.id).limit(1)
        )
        image = img_result.scalars().first()
        
        caption = (
            f"<b>{product.name}</b>\n\n"
            f"{product.description or ''}\n\n"
            f"💰 Цена: {product.price} ₽\n"
        )
        if product.old_price:
            caption += f"<s>{product.old_price} ₽</s>\n"
        
        # Кнопка "В корзину"
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_to_cart_{product.id}")]
        ])
        
        if image and image.telegram_file_id:
            await message.answer_photo(
                photo=image.telegram_file_id,
                caption=caption,
                reply_markup=keyboard
            )
        else:
            await message.answer(caption, reply_markup=keyboard)

@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_product_to_cart(callback: types.CallbackQuery, session: AsyncSession):
    """Добавляет товар в корзину по нажатию кнопки."""
    # Извлекаем ID товара из callback_data
    product_id = int(callback.data.split("_")[3])
    
    # Добавляем товар в корзину
    await add_to_cart(session, callback.from_user.id, product_id, 1)
    
    # Показываем всплывающее уведомление
    await callback.answer("✅ Товар добавлен в корзину!", show_alert=False)