from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from decimal import Decimal

from admin.states import EditProductStates
from database.models import Product, ProductImage, CartItem, OrderItem, Category

router = Router()

# --- Список товаров ---
@router.callback_query(F.data == "admin_products_manage")
async def list_products(callback: types.CallbackQuery, session: AsyncSession):
    """Показывает список всех товаров для управления."""
    result = await session.execute(select(Product).order_by(Product.id.desc()))
    products = result.scalars().all()

    if not products:
        text = "📦 Товаров пока нет."
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_products")]
        ])
    else:
        keyboard = []
        for p in products:
            status = "✅" if p.is_active else "❌"
            keyboard.append([
                InlineKeyboardButton(
                    text=f"{status} {p.name} — {p.price} ₽",
                    callback_data=f"admin_prod_view_{p.id}"
                )
            ])
        keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_products")])
        text = "📦 <b>Управление товарами</b>\n\nВыберите товар:"

    if callback.message.text:
        await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    else:
        await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
        try:
            await callback.message.delete()
        except Exception:
            pass

    await callback.answer()

# --- Просмотр товара ---
@router.callback_query(F.data.startswith("admin_prod_view_"))
async def view_product(callback: types.CallbackQuery, session: AsyncSession):
    """Показывает детали товара и действия."""
    product_id = int(callback.data.split("_")[3])
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()

    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return

    status = "✅ Активен" if product.is_active else "❌ Скрыт"
    text = (
        f"<b>{product.name}</b>\n\n"
        f"💰 Цена: {product.price} ₽\n"
        f"📦 Остаток: {product.stock}\n"
        f"Статус: {status}\n"
    )
    if product.description:
        text += f"\n📝 {product.description[:100]}...\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Скрыть/Показать", callback_data=f"admin_prod_toggle_{product.id}")],
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_prod_edit_{product.id}")],
        [InlineKeyboardButton(text="📁 Сменить категорию", callback_data=f"admin_prod_changecat_{product.id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_prod_delete_{product.id}")],
        [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="admin_products_manage")]
    ])

    img_result = await session.execute(
        select(ProductImage).where(ProductImage.product_id == product.id).limit(1)
    )
    image = img_result.scalars().first()

    if image and image.telegram_file_id:
        await callback.message.answer_photo(
            photo=image.telegram_file_id,
            caption=text,
            reply_markup=keyboard
        )
        try:
            await callback.message.delete()
        except Exception:
            pass
    else:
        if callback.message.text:
            await callback.message.edit_text(text, reply_markup=keyboard)
        else:
            await callback.message.answer(text, reply_markup=keyboard)
            try:
                await callback.message.delete()
            except Exception:
                pass

    await callback.answer()

# --- Скрыть/Показать ---
@router.callback_query(F.data.startswith("admin_prod_toggle_"))
async def toggle_product(callback: types.CallbackQuery, session: AsyncSession):
    product_id = int(callback.data.split("_")[3])
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()

    if product:
        product.is_active = not product.is_active
        await session.commit()
        await callback.answer("Статус изменен", show_alert=False)

    await list_products(callback, session)

# --- Удалить товар ---
@router.callback_query(F.data.startswith("admin_prod_delete_"))
async def delete_product(callback: types.CallbackQuery, session: AsyncSession):
    product_id = int(callback.data.split("_")[3])

    order_item_result = await session.execute(
        select(OrderItem).where(OrderItem.product_id == product_id).limit(1)
    )
    if order_item_result.scalars().first():
        await callback.answer(
            "❌ Нельзя удалить: товар есть в заказах. Сначала скройте его.",
            show_alert=True
        )
        return

    await session.execute(delete(CartItem).where(CartItem.product_id == product_id))
    await session.execute(delete(ProductImage).where(ProductImage.product_id == product_id))
    await session.execute(delete(Product).where(Product.id == product_id))
    await session.commit()

    await callback.answer("✅ Товар удален", show_alert=True)
    await list_products(callback, session)

# --- Быстрая смена категории ---
@router.callback_query(F.data.startswith("admin_prod_changecat_"))
async def change_category_start(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Быстрая смена категории товара."""
    product_id = int(callback.data.split("_")[3])
    
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    cat_result = await session.execute(select(Category).where(Category.is_active == True))
    categories = cat_result.scalars().all()

    if not categories:
        await callback.answer("Нет доступных категорий.", show_alert=True)
        return

    await state.update_data(quick_cat_product_id=product_id)
    
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(text=cat.name, callback_data=f"quick_cat_choose_{cat.id}")])
    keyboard.append([InlineKeyboardButton(text="Без категории", callback_data="quick_cat_choose_none")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_prod_view_{product_id}")])

    text = f"📁 <b>Смена категории для товара:</b> {product.name}\n\nВыберите новую категорию:"
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)

    # Проверяем, можно ли редактировать сообщение (если это фото — edit_text упадёт)
    if callback.message.text:
        await callback.message.edit_text(text, reply_markup=markup)
    else:
        await callback.message.answer(text, reply_markup=markup)
        try:
            await callback.message.delete()
        except Exception:
            pass

    await state.set_state(EditProductStates.waiting_for_quick_category)
    await callback.answer()

@router.callback_query(EditProductStates.waiting_for_quick_category, F.data.startswith("quick_cat_choose_"))
async def change_category_choose(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Применяет новую категорию к товару."""
    cat_data = callback.data.replace("quick_cat_choose_", "")
    
    if cat_data == "none":
        new_category_id = None
    else:
        new_category_id = int(cat_data)

    data = await state.get_data()
    product_id = data.get("quick_cat_product_id")
    
    if not product_id:
        await callback.answer("Ошибка: товар не найден в состоянии", show_alert=True)
        await state.clear()
        return

    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    
    if product:
        product.category_id = new_category_id
        await session.commit()
        await callback.answer("✅ Категория изменена", show_alert=True)
        
        # Возвращаемся к карточке товара
        class FakeCallback:
            def __init__(self, original):
                self.message = original.message
                self.from_user = original.from_user
                self.data = f"admin_prod_view_{product_id}"
                self.id = original.id
                self.bot = original.bot
        
        await view_product(FakeCallback(callback), session)
    else:
        await callback.answer("❌ Товар не найден", show_alert=True)
    
    await state.clear()

# --- Редактирование товара (старый функционал) ---
@router.callback_query(F.data.startswith("admin_prod_edit_"))
async def edit_product_start(callback: types.CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[3])
    await state.update_data(edit_product_id=product_id)
    await callback.message.answer("Введите новое название товара (или /skip чтобы пропустить):")
    await state.set_state(EditProductStates.waiting_for_name)
    await callback.answer()

@router.message(EditProductStates.waiting_for_name)
async def edit_product_name(message: types.Message, state: FSMContext):
    if message.text != "/skip":
        await state.update_data(edit_name=message.text)
    else:
        await state.update_data(edit_name=None)
    await message.answer("Введите новую цену (или /skip):")
    await state.set_state(EditProductStates.waiting_for_price)

@router.message(EditProductStates.waiting_for_price)
async def edit_product_price(message: types.Message, state: FSMContext):
    if message.text != "/skip":
        try:
            price = Decimal(message.text.replace(",", "."))
            await state.update_data(edit_price=price)
        except:
            await message.answer("❌ Ошибка. Введите число или /skip:")
            return
    else:
        await state.update_data(edit_price=None)
    await message.answer("Введите новый остаток (или /skip):")
    await state.set_state(EditProductStates.waiting_for_stock)

@router.message(EditProductStates.waiting_for_stock)
async def edit_product_stock(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text != "/skip":
        try:
            stock = int(message.text)
            await state.update_data(edit_stock=stock)
        except:
            await message.answer("❌ Ошибка. Введите целое число или /skip:")
            return
    else:
        await state.update_data(edit_stock=None)

    await message.answer(
        "Хотите изменить категорию товара?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Да, изменить", callback_data="edit_cat_yes")],
            [InlineKeyboardButton(text="Нет, оставить", callback_data="edit_cat_no")]
        ])
    )
    await state.set_state(EditProductStates.waiting_for_category)

@router.callback_query(EditProductStates.waiting_for_category, F.data == "edit_cat_yes")
async def edit_category_start(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    result = await session.execute(select(Category).where(Category.is_active == True))
    categories = result.scalars().all()

    if not categories:
        await callback.message.answer("Нет доступных категорий.")
        await finish_edit(callback.message, state, session, new_category_id=None)
        await callback.answer()
        return

    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(text=cat.name, callback_data=f"edit_cat_choose_{cat.id}")])
    keyboard.append([InlineKeyboardButton(text="Без категории", callback_data="edit_cat_choose_none")])

    await callback.message.answer(
        "Выберите новую категорию:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
    )
    await callback.answer()

@router.callback_query(EditProductStates.waiting_for_category, F.data == "edit_cat_no")
async def edit_category_no(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await finish_edit(callback.message, state, session, new_category_id=None)
    await callback.answer()

@router.callback_query(EditProductStates.waiting_for_category, F.data.startswith("edit_cat_choose_"))
async def edit_category_choose(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    cat_data = callback.data.replace("edit_cat_choose_", "")
    if cat_data == "none":
        new_category_id = None
    else:
        new_category_id = int(cat_data)

    await finish_edit(callback.message, state, session, new_category_id=new_category_id)
    await callback.answer()

async def finish_edit(message: types.Message, state: FSMContext, session: AsyncSession, new_category_id: int = None):
    """Завершает редактирование товара, сохраняя изменения."""
    data = await state.get_data()
    product_id = data.get("edit_product_id")

    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()

    if product:
        if data.get("edit_name"):
            product.name = data["edit_name"]
        if data.get("edit_price"):
            product.price = data["edit_price"]
        if data.get("edit_stock") is not None:
            product.stock = data["edit_stock"]
        if new_category_id is not None:
            product.category_id = new_category_id
        await session.commit()
        await message.answer("✅ Товар обновлен.")
    else:
        await message.answer("❌ Товар не найден.")

    await state.clear()