from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from config import ADMIN_ID
from database.models import UserEvent, User, PlatformAccount

router = Router()

@router.callback_query(F.data == "admin_analytics")
async def show_analytics(callback: types.CallbackQuery, session: AsyncSession):
    """Показывает аналитику по событиям."""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Нет доступа.", show_alert=True)
        return

    # 1. Общая воронка
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
    
    if views > 0:
        conv = (orders / views) * 100
        text += f"\n📈 Конверсия просмотров в заказы: {conv:.1f}%"
    
    # 2. Шаги оформления (отвалы)
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

    # 3. Последние события с детализацией
    text += "\n<b>Последние 10 событий:</b>\n"
    events_result = await session.execute(
        select(UserEvent)
        .options(selectinload(UserEvent.user))  # загружаем пользователя
        .order_by(UserEvent.created_at.desc())
        .limit(10)
    )
    events = events_result.scalars().all()
    
    for ev in events:
        user_name = ev.user.full_name if ev.user else "Неизвестный"
        time_str = ev.created_at.strftime("%H:%M")
        
        if ev.event_type == "product_view":
            product_name = ev.event_data.get("product_name", "Товар") if ev.event_data else "Товар"
            text += f"👁 {time_str} {user_name} смотрел: {product_name}\n"
        elif ev.event_type == "add_to_cart":
            product_id = ev.event_data.get("product_id", "?") if ev.event_data else "?"
            text += f"🛒 {time_str} {user_name} добавил товар ID {product_id}\n"
        elif ev.event_type == "checkout_start":
            text += f"📝 {time_str} {user_name} начал оформление\n"
        elif ev.event_type == "order_created":
            order_id = ev.event_data.get("order_id", "?") if ev.event_data else "?"
            total = ev.event_data.get("total", "?") if ev.event_data else "?"
            text += f"✅ {time_str} {user_name} оформил заказ #{order_id} на {total} ₽\n"
        elif ev.event_type == "checkout_abandon":
            text += f"❌ {time_str} {user_name} бросил оформление\n"
        else:
            text += f"• {time_str} {user_name}: {ev.event_type}\n"

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