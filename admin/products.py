from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from admin.states import AddProductStates
from admin.keyboards import get_cancel_keyboard, get_skip_keyboard, get_categories_keyboard, get_confirm_keyboard
from database.models import Product, Category, ProductImage
from decimal import Decimal

router = Router()

# --- Шаг 1: Начало добавления товара ---
@router.callback_query(F.data == "admin_products")
async def start_add_product(callback: types.CallbackQuery, state: FSMContext):
    """Начинает процесс добавления товара."""
    await callback.message.answer(
        "📝 <b>Добавление товара</b>\n\nШаг 1 из 8: Введите название товара:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddProductStates.waiting_for_name)
    await callback.answer()

# --- Шаг 2: Название ---
@router.message(AddProductStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Добавление товара отменено.", reply_markup=types.ReplyKeyboardRemove())
        return
    
    await state.update_data(name=message.text)
    await message.answer(
        "Шаг 2 из 8: Введите описание товара (или нажмите 'Пропустить'):",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(AddProductStates.waiting_for_description)

# --- Шаг 3: Описание ---
@router.message(AddProductStates.waiting_for_description)
async def process_description(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=types.ReplyKeyboardRemove())
        return
    
    description = None if message.text == "⏩ Пропустить" else message.text
    await state.update_data(description=description)
    await message.answer(
        "Шаг 3 из 8: Введите цену товара (только число, например 4990):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddProductStates.waiting_for_price)

# --- Шаг 4: Цена ---
@router.message(AddProductStates.waiting_for_price)
async def process_price(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=types.ReplyKeyboardRemove())
        return
    
    try:
        price = Decimal(message.text.replace(",", "."))
    except:
        await message.answer("❌ Ошибка. Введите цену числом (например 4990):")
        return
    
    await state.update_data(price=price)
    await message.answer(
        "Шаг 4 из 8: Введите старую цену (для скидки) или нажмите 'Пропустить':",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(AddProductStates.waiting_for_old_price)

# --- Шаг 5: Старая цена ---
@router.message(AddProductStates.waiting_for_old_price)
async def process_old_price(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=types.ReplyKeyboardRemove())
        return
    
    old_price = None
    if message.text != "⏩ Пропустить":
        try:
            old_price = Decimal(message.text.replace(",", "."))
        except:
            await message.answer("❌ Ошибка. Введите число или нажмите 'Пропустить':")
            return
    
    await state.update_data(old_price=old_price)
    await message.answer(
        "Шаг 5 из 8: Отправьте фотографию товара (или нажмите 'Пропустить'):",
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(AddProductStates.waiting_for_photo)

# --- Шаг 6: Фото ---
@router.message(AddProductStates.waiting_for_photo, F.photo | F.text)
async def process_photo(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=types.ReplyKeyboardRemove())
        return
    
    photo_id = None
    if message.photo:
        photo_id = message.photo[-1].file_id  # Берем самое большое фото
    elif message.text != "⏩ Пропустить":
        await message.answer("❌ Пожалуйста, отправьте фото или нажмите 'Пропустить'.")
        return

    await state.update_data(photo_id=photo_id)
    
    # Получаем категории из БД
    result = await session.execute(select(Category).where(Category.is_active == True))
    categories = result.scalars().all()
    
    if not categories:
        await message.answer("⚠️ В базе нет категорий. Товар будет добавлен без категории.")
        await state.update_data(category_id=None)
        await message.answer(
            "Шаг 7 из 8: Введите остаток на складе (число, например 10):",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AddProductStates.waiting_for_stock)
        return

    await message.answer(
        "Шаг 6 из 8: Выберите категорию для товара:",
        reply_markup=get_categories_keyboard(categories)
    )
    await state.set_state(AddProductStates.waiting_for_category)

# --- Шаг 7: Категория (Callback) ---
@router.callback_query(AddProductStates.waiting_for_category, F.data.startswith("cat_"))
async def process_category(callback: types.CallbackQuery, state: FSMContext):
    cat_data = callback.data
    
    if cat_data == "cat_none":
        category_id = None
    else:
        category_id = int(cat_data.split("_")[1])
    
    await state.update_data(category_id=category_id)
    
    await callback.message.answer(
        "Шаг 7 из 8: Введите остаток на складе (число, например 10):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AddProductStates.waiting_for_stock)
    await callback.answer()

# --- Шаг 8: Остаток ---
@router.message(AddProductStates.waiting_for_stock)
async def process_stock(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=types.ReplyKeyboardRemove())
        return
    
    try:
        stock = int(message.text)
    except:
        await message.answer("❌ Ошибка. Введите целое число:")
        return
    
    await state.update_data(stock=stock)
    
    # Показываем предпросмотр
    data = await state.get_data()
    preview = (
        f"<b>Предпросмотр товара:</b>\n\n"
        f"📌 Название: {data['name']}\n"
        f"📝 Описание: {data['description'] or 'Нет'}\n"
        f"💰 Цена: {data['price']} ₽\n"
        f"🏷 Старая цена: {data['old_price'] or 'Нет'}\n"
        f"📦 Остаток: {data['stock']}\n"
    )
    
    if data.get('photo_id'):
        await message.answer_photo(photo=data['photo_id'], caption=preview, reply_markup=get_confirm_keyboard())
    else:
        await message.answer(preview, reply_markup=get_confirm_keyboard())
    
    await state.set_state(AddProductStates.waiting_for_confirm)

# --- Шаг 9: Сохранение ---
@router.callback_query(AddProductStates.waiting_for_confirm, F.data == "product_save")
async def save_product(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    
    # Создаем товар
    new_product = Product(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        old_price=data['old_price'],
        stock=data['stock'],
        category_id=data.get('category_id'),
        is_active=True
    )
    session.add(new_product)
    await session.flush() # Получаем ID товара
    
    # Если есть фото, сохраняем его
    if data.get('photo_id'):
        new_image = ProductImage(
            product_id=new_product.id,
            image_url="", # Пока оставим пустым, так как храним file_id
            telegram_file_id=data['photo_id']
        )
        session.add(new_image)
    
    await session.commit()
    
    await callback.message.edit_text("✅ Товар успешно добавлен в каталог!")
    await state.clear()
    await callback.answer()

# --- Отмена на этапе подтверждения ---
@router.callback_query(AddProductStates.waiting_for_confirm, F.data == "product_cancel")
async def cancel_product(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Добавление товара отменено.")
    await callback.answer()