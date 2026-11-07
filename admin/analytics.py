from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from config import ADMIN_ID
from database.models import UserEvent, User

router = Router()

@router.callback_query(F.data == "admin_analytics")
async def show_analytics(callback: types.CallbackQuery, session: AsyncSession):
    """Показывает аналитику по событиям."""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    # Считаем воронку
    views = await _count_events(session, "product_view")
    add_carts = await _count_events(session, "add_to_cart")
    checkouts = await _count_events(session, "checkout_start")
    orders = await _count_events(session, "order_created")
    
    text = (
        f"📊 <b>Воронка продаж</b>\n\n"
        f"👁 Просмотры товаров: {views}\n"
        f"🛒 Добавления в корзину: {add_carts}\n"
        f"📝 Начали оформление: {checkouts}\n"
        f"✅ Успешные заказы: {orders}\n"
    )
    
    # Вычисляем конверсию
    if views > 0:
        conv = (orders / views) * 100
        text += f"\n📈 Конверсия просмотров в заказы: {conv:.1f}%"
    
    # Шаги отвала
    step_names = await _count_events(session, "checkout_step_name")
    step_phone = await _count_events(session, "checkout_step_phone")
    step_delivery = await _count_events(session, "checkout_step_delivery")
    step_address = await _count_events(session, "checkout_step_address")
    step_comment = await _count_events(session, "checkout_step_comment")
    
    text += f"\n\n<b>Шаги оформления:</b>\n"
    text += f"1. Имя: {step_names}\n"
    text += f"2. Телефон: {step_phone}\n"
    text += f"3. Доставка: {step_delivery}\n"
    text += f"4. Адрес: {step_address}\n"
    text += f"5. Комментарий: {step_comment}\n"

    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="admin_back")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

async def _count_events(session: AsyncSession, event_type: str) -> int:
    result = await session.execute(
        select(func.count(UserEvent.id)).where(UserEvent.event_type == event_type)
    )
    return result.scalar() or 0