from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from services.cart import (
    get_cart_items, add_to_cart, update_quantity, remove_item, clear_cart, get_cart_total
)
from platforms.telegram.keyboards import get_cart_keyboard

router = Router()

@router.message(F.text == "Корзина")
async def show_cart(message: types.Message, session: AsyncSession):
    """Показывает содержимое корзины."""
    items = await get_cart_items(session, message.from_user.id)
    
    if not items:
        await message.answer("🛒 Ваша корзина пуста.")
        return
    
    total = await get_cart_total(session, message.from_user.id)
    text = "🛒 <b>Ваша корзина:</b>\n\n"
    
    await message.answer(text, reply_markup=get_cart_keyboard(items))

# --- Обработчики кнопок корзины (Callback) ---

@router.callback_query(F.data.startswith("cart_plus_"))
async def cart_plus(callback: types.CallbackQuery, session: AsyncSession):
    item_id = int(callback.data.split("_")[2])
    await update_quantity(session, item_id, 1)
    # Обновляем сообщение
    items = await get_cart_items(session, callback.from_user.id)
    if items:
        await callback.message.edit_reply_markup(reply_markup=get_cart_keyboard(items))
    else:
        await callback.message.edit_text("🛒 Корзина пуста.")
    await callback.answer()

@router.callback_query(F.data.startswith("cart_minus_"))
async def cart_minus(callback: types.CallbackQuery, session: AsyncSession):
    item_id = int(callback.data.split("_")[2])
    await update_quantity(session, item_id, -1)
    items = await get_cart_items(session, callback.from_user.id)
    if items:
        await callback.message.edit_reply_markup(reply_markup=get_cart_keyboard(items))
    else:
        await callback.message.edit_text("🛒 Корзина пуста.")
    await callback.answer()

@router.callback_query(F.data.startswith("cart_del_"))
async def cart_del(callback: types.CallbackQuery, session: AsyncSession):
    item_id = int(callback.data.split("_")[2])
    await remove_item(session, item_id)
    items = await get_cart_items(session, callback.from_user.id)
    if items:
        await callback.message.edit_reply_markup(reply_markup=get_cart_keyboard(items))
    else:
        await callback.message.edit_text("🛒 Корзина пуста.")
    await callback.answer()

@router.callback_query(F.data == "cart_clear")
async def cart_clear(callback: types.CallbackQuery, session: AsyncSession):
    await clear_cart(session, callback.from_user.id)
    await callback.message.edit_text("🛒 Корзина очищена.")
    await callback.answer()