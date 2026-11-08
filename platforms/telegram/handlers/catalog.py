from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.models import Product, ProductImage, Category
from services.cart import add_to_cart
from services.analytics import log_event

router = Router()

# --- Показ категорий ---
@router.message(F.text == "Каталог")
async def show_categories(message: types.Message, session: AsyncSession):
    """Показывает родительские категории."""
    result = await session.execute(
        select(Category).where(Category.parent_id == None, Category.is_active == True).order_by(Category.sort_order)
    )
    categories = result.scalars().all()

    if not categories:
        # Если категорий нет, показываем все товары
        await show_all_products(message, session)
        return

    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(text=cat.name, callback_data=f"cat_open_{cat.id}")])
    keyboard.append([InlineKeyboardButton(text="📦 Все товары", callback_data="cat_all")])

    await message.answer(
        "📁 <b>Выберите категорию:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )


@router.callback_query(F.data.startswith("cat_open_"))
async def open_category(callback: types.CallbackQuery, session: AsyncSession):
    """Открывает категорию: показывает подкатегории или товары."""
    cat_id = int(callback.data.split("_")[2])
    result = await session.execute(select(Category).where(Category.id == cat_id))
    category = result.scalars().first()
    if not category:
        await callback.answer("Категория не найдена", show_alert=True)
        return

    # Ищем подкатегории
    sub_result = await session.execute(
        select(Category).where(Category.parent_id == cat_id, Category.is_active == True).order_by(Category.sort_order)
    )
    subcategories = sub_result.scalars().all()

    if subcategories:
        keyboard = []
        for sub in subcategories:
            keyboard.append([InlineKeyboardButton(text=sub.name, callback_data=f"cat_open_{sub.id}")])
        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="cat_back")])
        await callback.message.edit_text(
            f"📁 <b>{category.name}</b>\n\nВыберите подкатегорию:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    else:
        # Показываем товары этой категории
        await show_products_by_category(callback.message, session, cat_id, category.name)

    await callback.answer()


@router.callback_query(F.data == "cat_all")
async def show_all_products_callback(callback: types.CallbackQuery, session: AsyncSession):
    await show_all_products(callback.message, session)
    await callback.answer()


@router.callback_query(F.data == "cat_back")
async def back_to_categories(callback: types.CallbackQuery, session: AsyncSession):
    result = await session.execute(
        select(Category).where(Category.parent_id == None, Category.is_active == True).order_by(Category.sort_order)
    )
    categories = result.scalars().all()
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(text=cat.name, callback_data=f"cat_open_{cat.id}")])
    keyboard.append([InlineKeyboardButton(text="📦 Все товары", callback_data="cat_all")])
    await callback.message.edit_text(
        "📁 <b>Выберите категорию:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()


async def show_products_by_category(message: types.Message, session: AsyncSession, category_id: int, category_name: str):
    result = await session.execute(
        select(Product).where(Product.category_id == category_id, Product.is_active == True)
    )
    products = result.scalars().all()

    if not products:
        await message.edit_text(f"😔 В категории '{category_name}' пока нет товаров.")
        return

    await message.edit_text(f"📦 <b>Товары в категории '{category_name}':</b>")
    for product in products:
        await send_product_card(message, session, product)


async def show_all_products(message: types.Message, session: AsyncSession):
    result = await session.execute(select(Product).where(Product.is_active == True))
    products = result.scalars().all()

    if not products:
        await message.answer("😔 В каталоге пока нет товаров.")
        return

    for product in products:
        await send_product_card(message, session, product)


async def send_product_card(message: types.Message, session: AsyncSession, product: Product):
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
    if product.stock <= 0:
        caption += "\n❌ <b>Нет в наличии</b>"
    else:
        caption += f"\n📦 В наличии: {product.stock} шт."

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 В корзину", callback_data=f"add_to_cart_{product.id}")],
        [InlineKeyboardButton(text="❓ Задать вопрос", callback_data=f"product_question_{product.id}")]
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
    product_id = int(callback.data.split("_")[3])
    try:
        await add_to_cart(session, callback.from_user.id, product_id, 1)
        await log_event(
            session, callback.from_user.id, "add_to_cart", {"product_id": product_id}
        )
        await callback.answer("✅ Товар добавлен в корзину!", show_alert=False)
    except ValueError as e:
        await callback.answer(f"❌ {str(e)}", show_alert=True)