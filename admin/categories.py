from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from admin.states import CategoryStates
from admin.keyboards import get_categories_admin_keyboard, get_category_actions_keyboard
from database.models import Category, Product

router = Router()

@router.callback_query(F.data == "admin_categories")
async def list_categories(callback: types.CallbackQuery, session: AsyncSession):
    """Показывает список категорий."""
    result = await session.execute(select(Category).order_by(Category.sort_order))
    categories = result.scalars().all()
    
    await callback.message.edit_text(
        "📁 <b>Управление категориями</b>\n\nВыберите категорию для управления:",
        reply_markup=get_categories_admin_keyboard(categories)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("admin_cat_view_"))
async def view_category(callback: types.CallbackQuery, session: AsyncSession):
    """Показывает действия с конкретной категорией."""
    cat_id = int(callback.data.split("_")[3])
    result = await session.execute(select(Category).where(Category.id == cat_id))
    cat = result.scalars().first()
    
    if not cat:
        await callback.answer("Категория не найдена", show_alert=True)
        return
        
    text = f"📁 <b>Категория:</b> {cat.name}\nСтатус: {'Активна' if cat.is_active else 'Скрыта'}"
    await callback.message.edit_text(text, reply_markup=get_category_actions_keyboard(cat.id))
    await callback.answer()

# --- Добавление категории ---
@router.callback_query(F.data == "admin_cat_add")
async def add_category_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите название новой категории:")
    await state.set_state(CategoryStates.waiting_for_name)
    await callback.answer()

@router.message(CategoryStates.waiting_for_name)
async def add_category_process(message: types.Message, state: FSMContext, session: AsyncSession):
    new_cat = Category(name=message.text)
    session.add(new_cat)
    await session.commit()
    await message.answer(f"✅ Категория '{message.text}' успешно добавлена.")
    await state.clear()
    
    # Возвращаемся к списку
    result = await session.execute(select(Category).order_by(Category.sort_order))
    categories = result.scalars().all()
    await message.answer(
        "📁 <b>Управление категориями</b>\n\nВыберите категорию для управления:",
        reply_markup=get_categories_admin_keyboard(categories)
    )

# --- Редактирование категории ---
@router.callback_query(F.data.startswith("admin_cat_edit_"))
async def edit_category_start(callback: types.CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split("_")[3])
    await state.update_data(edit_cat_id=cat_id)
    await callback.message.answer("Введите новое название категории:")
    await state.set_state(CategoryStates.waiting_for_edit_name)
    await callback.answer()

@router.message(CategoryStates.waiting_for_edit_name)
async def edit_category_process(message: types.Message, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    cat_id = data['edit_cat_id']
    
    result = await session.execute(select(Category).where(Category.id == cat_id))
    cat = result.scalars().first()
    
    if cat:
        cat.name = message.text
        await session.commit()
        await message.answer(f"✅ Категория переименована в '{message.text}'.")
    else:
        await message.answer("❌ Категория не найдена.")
        
    await state.clear()
    
    # Возвращаемся к списку
    result = await session.execute(select(Category).order_by(Category.sort_order))
    categories = result.scalars().all()
    await message.answer(
        "📁 <b>Управление категориями</b>\n\nВыберите категорию для управления:",
        reply_markup=get_categories_admin_keyboard(categories)
    )

# --- Скрытие/Показ категории ---
@router.callback_query(F.data.startswith("admin_cat_toggle_"))
async def toggle_category(callback: types.CallbackQuery, session: AsyncSession):
    cat_id = int(callback.data.split("_")[3])
    result = await session.execute(select(Category).where(Category.id == cat_id))
    cat = result.scalars().first()
    
    if cat:
        cat.is_active = not cat.is_active
        await session.commit()
        await callback.answer("Статус изменен", show_alert=False)
        
    # Возвращаемся к списку
    result = await session.execute(select(Category).order_by(Category.sort_order))
    categories = result.scalars().all()
    await callback.message.edit_text(
        "📁 <b>Управление категориями</b>\n\nВыберите категорию для управления:",
        reply_markup=get_categories_admin_keyboard(categories)
    )

# --- Удаление категории ---
@router.callback_query(F.data.startswith("admin_cat_del_"))
async def delete_category(callback: types.CallbackQuery, session: AsyncSession):
    cat_id = int(callback.data.split("_")[3])
    
    # Переносим товары в "Без категории" (category_id = None)
    await session.execute(
        update(Product).where(Product.category_id == cat_id).values(category_id=None)
    )
    # Удаляем категорию
    await session.execute(delete(Category).where(Category.id == cat_id))
    await session.commit()
    
    await callback.answer("Категория удалена. Товары перемещены в 'Без категории'.", show_alert=True)
    
    # Возвращаемся к списку
    result = await session.execute(select(Category).order_by(Category.sort_order))
    categories = result.scalars().all()
    await callback.message.edit_text(
        "📁 <b>Управление категориями</b>\n\nВыберите категорию для управления:",
        reply_markup=get_categories_admin_keyboard(categories)
    )