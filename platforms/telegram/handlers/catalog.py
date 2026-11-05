from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.models import Product, Category, ProductImage
from platforms.telegram.keyboards import get_main_menu_keyboard

router = Router()

@router.message(F.text == "Каталог")  # Ловим нажатие на кнопку "Каталог"
async def show_catalog(message: types.Message, session: AsyncSession):
    """Показывает каталог: список категорий или товаров."""
    
    # 1. Проверяем, есть ли категории
    result = await session.execute(select(Category).where(Category.is_active == True))
    categories = result.scalars().all()
    
    if categories:
        # Если категории есть, показываем их список (пока просто текстом)
        text = "📁 <b>Выберите категорию:</b>\n\n"
        for cat in categories:
            text += f"• {cat.name}\n"
        
        await message.answer(text)
        # TODO: Добавить inline-клавиатуру для выбора категории
    else:
        # Если категорий нет, показываем все товары
        result = await session.execute(select(Product).where(Product.is_active == True))
        products = result.scalars().all()
        
        if not products:
            await message.answer("😔 В каталоге пока нет товаров.")
            return
        
        await message.answer(f"🛍 <b>Все товары ({len(products)}):</b>")
        
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
            
            if image and image.telegram_file_id:
                await message.answer_photo(
                    photo=image.telegram_file_id,
                    caption=caption
                )
            else:
                await message.answer(caption)