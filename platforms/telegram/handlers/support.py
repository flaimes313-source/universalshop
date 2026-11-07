from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from services.settings import get_setting
from database.models import Product
from sqlalchemy import select

router = Router()

class SupportStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_reply = State()
    waiting_for_product_question = State()

# ==========================================
# Поддержка (общие вопросы)
# ==========================================

@router.message(F.text == "Контакты")
async def start_support(message: types.Message, state: FSMContext, session: AsyncSession):
    """Начинает диалог поддержки."""
    enabled = await get_setting(session, "support_enabled", "1")
    if enabled != "1":
        await message.answer("Поддержка временно отключена.")
        return

    text = await get_setting(session, "support_text", "Напишите ваш вопрос, и мы ответим вам в ближайшее время.")
    await message.answer(text)
    await state.set_state(SupportStates.waiting_for_message)

@router.message(SupportStates.waiting_for_message)
async def send_support_message(message: types.Message, state: FSMContext):
    """Пересылает сообщение поддержки админу."""
    if ADMIN_ID:
        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✏️ Ответить", callback_data=f"support_reply_{message.from_user.id}")]
            ])
            await message.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📩 <b>Новое сообщение в поддержку</b>\n\n"
                     f"👤 От: {message.from_user.full_name} (ID: {message.from_user.id})\n"
                     f"💬 Текст: {message.text}",
                reply_markup=keyboard
            )
            await message.answer("✅ Ваше сообщение отправлено. Мы ответим вам в ближайшее время.")
        except Exception as e:
            await message.answer("❌ Не удалось отправить сообщение. Попробуйте позже.")
            print(f"Ошибка отправки в поддержку: {e}")
    else:
        await message.answer("❌ Администратор не настроен.")
    await state.clear()

# ==========================================
# Вопрос о товаре
# ==========================================

@router.callback_query(F.data.startswith("product_question_"))
async def start_product_question(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    """Начинает диалог вопроса о конкретном товаре."""
    product_id = int(callback.data.split("_")[2])
    
    # Получаем название товара
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalars().first()
    product_name = product.name if product else "Товар"
    
    await state.update_data(question_product_id=product_id, question_product_name=product_name)
    
    await callback.message.answer(
        f"❓ <b>Вопрос о товаре:</b> {product_name}\n\n"
        f"Напишите ваш вопрос, и мы ответим вам в ближайшее время."
    )
    await state.set_state(SupportStates.waiting_for_product_question)
    await callback.answer()

@router.message(SupportStates.waiting_for_product_question)
async def send_product_question(message: types.Message, state: FSMContext):
    """Пересылает вопрос о товаре админу."""
    data = await state.get_data()
    product_name = data.get("question_product_name", "Товар")
    
    if ADMIN_ID:
        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="✏️ Ответить", 
                    callback_data=f"support_reply_{message.from_user.id}"
                )]
            ])
            await message.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"❓ <b>Вопрос о товаре:</b> {product_name}\n\n"
                     f"👤 От: {message.from_user.full_name} (ID: {message.from_user.id})\n"
                     f"💬 Текст: {message.text}",
                reply_markup=keyboard
            )
            await message.answer("✅ Ваш вопрос отправлен. Мы ответим вам в ближайшее время.")
        except Exception as e:
            await message.answer("❌ Не удалось отправить вопрос. Попробуйте позже.")
            print(f"Ошибка отправки вопроса о товаре: {e}")
    else:
        await message.answer("❌ Администратор не настроен.")
    
    await state.clear()

# ==========================================
# Ответ поддержки
# ==========================================

@router.callback_query(F.data.startswith("support_reply_"))
async def reply_to_support_start(callback: types.CallbackQuery, state: FSMContext):
    """Начинает процесс ответа пользователю."""
    user_id = int(callback.data.split("_")[2])
    await state.update_data(reply_to_user=user_id)
    await callback.message.answer("Введите ответ для пользователя:")
    await state.set_state(SupportStates.waiting_for_reply)
    await callback.answer()

@router.message(SupportStates.waiting_for_reply)
async def send_reply_to_user(message: types.Message, state: FSMContext):
    """Отправляет ответ пользователю."""
    data = await state.get_data()
    user_id = data.get("reply_to_user")
    if user_id:
        try:
            await message.bot.send_message(
                chat_id=user_id,
                text=f"📩 <b>Ответ поддержки:</b>\n\n{message.text}"
            )
            await message.answer("✅ Ответ отправлен.")
        except Exception as e:
            await message.answer(f"❌ Ошибка: {e}")
        await state.clear()
    else:
        await message.answer("Не найден пользователь для ответа.")