from aiogram import Router, types, F
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from database.models import Order, User, Product, OrderItem
from admin.menu import get_admin_main_menu

router = Router()

def get_statistics_keyboard() -> types.InlineKeyboardMarkup:
    """Клавиатура выбора периода статистики."""
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📅 Сегодня", callback_data="stats_today")],
        [types.InlineKeyboardButton(text="📅 Вчера", callback_data="stats_yesterday")],
        [types.InlineKeyboardButton(text="📅 Последние 7 дней", callback_data="stats_7days")],
        [types.InlineKeyboardButton(text="📅 Последние 30 дней", callback_data="stats_30days")],
        [types.InlineKeyboardButton(text="📅 За всё время", callback_data="stats_all")],
        [types.InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="admin_back")]
    ])

async def _get_statistics_text(session: AsyncSession, start_date: datetime = None) -> str:
    """Формирует текст статистики за период."""
    # Базовый запрос
    query = select(Order)
    if start_date:
        query = query.where(Order.created_at >= start_date)
    
    result = await session.execute(query)
    orders = result.scalars().all()
    
    if not orders:
        return "📊 За выбранный период заказов нет."
    
    total_orders = len(orders)
    paid_orders = [o for o in orders if o.status in ("paid", "processing", "shipped", "completed")]
    revenue = sum(o.total_amount for o in paid_orders)
    avg_check = revenue / len(paid_orders) if paid_orders else Decimal("0")
    
    # Количество новых пользователей (упрощенно — за все время)
    user_query = select(func.count(User.id))
    if start_date:
        user_query = user_query.where(User.created_at >= start_date)
    user_result = await session.execute(user_query)
    users_count = user_result.scalar() or 0
    
    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"📦 Всего заказов: {total_orders}\n"
        f"✅ Оплаченных: {len(paid_orders)}\n"
        f"💰 Выручка: {revenue} ₽\n"
        f"📈 Средний чек: {avg_check:.2f} ₽\n"
        f"👥 Новых пользователей: {users_count}\n"
    )
    return text

@router.callback_query(F.data == "admin_statistics")
async def show_statistics_menu(callback: types.CallbackQuery):
    """Показывает меню выбора периода."""
    await callback.message.edit_text(
        "📊 <b>Статистика</b>\n\nВыберите период:",
        reply_markup=get_statistics_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "stats_today")
async def stats_today(callback: types.CallbackQuery, session: AsyncSession):
    start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    text = await _get_statistics_text(session, start)
    await callback.message.edit_text(text, reply_markup=get_statistics_keyboard())
    await callback.answer()

@router.callback_query(F.data == "stats_yesterday")
async def stats_yesterday(callback: types.CallbackQuery, session: AsyncSession):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    text = await _get_statistics_text(session, yesterday_start)
    await callback.message.edit_text(text, reply_markup=get_statistics_keyboard())
    await callback.answer()

@router.callback_query(F.data == "stats_7days")
async def stats_7days(callback: types.CallbackQuery, session: AsyncSession):
    start = datetime.now(timezone.utc) - timedelta(days=7)
    text = await _get_statistics_text(session, start)
    await callback.message.edit_text(text, reply_markup=get_statistics_keyboard())
    await callback.answer()

@router.callback_query(F.data == "stats_30days")
async def stats_30days(callback: types.CallbackQuery, session: AsyncSession):
    start = datetime.now(timezone.utc) - timedelta(days=30)
    text = await _get_statistics_text(session, start)
    await callback.message.edit_text(text, reply_markup=get_statistics_keyboard())
    await callback.answer()

@router.callback_query(F.data == "stats_all")
async def stats_all(callback: types.CallbackQuery, session: AsyncSession):
    text = await _get_statistics_text(session, None)
    await callback.message.edit_text(text, reply_markup=get_statistics_keyboard())
    await callback.answer()