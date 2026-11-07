from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.models import Order, OrderItem, User, PlatformAccount
from admin.menu import get_admin_main_menu

router = Router()

STATUS_NAMES = {
    "new": "🆕 Новый",
    "pending_payment": "⏳ Ожидает оплаты",
    "paid": "✅ Оплачен",
    "processing": "📦 В обработке",
    "shipped": "🚚 Отправлен",
    "completed": "🏁 Выполнен",
    "cancelled": "❌ Отменён",
}

def get_admin_orders_keyboard(orders: list[Order]) -> types.InlineKeyboardMarkup:
    """Клавиатура со списком заказов."""
    keyboard = []
    for order in orders:
        status_emoji = STATUS_NAMES.get(order.status, order.status).split()[0]
        keyboard.append([
            types.InlineKeyboardButton(
                text=f"{status_emoji} Заказ #{order.id} — {order.total_amount} ₽",
                callback_data=f"admin_order_view_{order.id}"
            )
        ])
    keyboard.append([types.InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="admin_back")])
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_order_status_keyboard(order_id: int, current_status: str) -> types.InlineKeyboardMarkup:
    """Клавиатура для смены статуса заказа."""
    keyboard = []
    for status_key, status_name in STATUS_NAMES.items():
        if status_key == current_status:
            continue
        keyboard.append([
            types.InlineKeyboardButton(
                text=status_name,
                callback_data=f"admin_order_setstatus_{order_id}_{status_key}"
            )
        ])
    keyboard.append([types.InlineKeyboardButton(text="🔙 Назад к списку", callback_data="admin_orders_list")])
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard)


@router.callback_query(F.data == "admin_orders")
async def admin_orders_list(callback: types.CallbackQuery, session: AsyncSession):
    """Показывает список всех заказов."""
    result = await session.execute(
        select(Order).order_by(Order.created_at.desc()).limit(20)
    )
    orders = result.scalars().all()

    if not orders:
        await callback.message.edit_text(
            "📋 Заказов пока нет.",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
            ])
        )
        await callback.answer()
        return

    text = "📋 <b>Последние заказы:</b>\n\nВыберите заказ для просмотра:"
    await callback.message.edit_text(text, reply_markup=get_admin_orders_keyboard(orders))
    await callback.answer()


@router.callback_query(F.data == "admin_orders_list")
async def admin_orders_list_callback(callback: types.CallbackQuery, session: AsyncSession):
    """Обработчик для кнопки 'Назад к списку'."""
    await admin_orders_list(callback, session)


@router.callback_query(F.data.startswith("admin_order_view_"))
async def admin_order_view(callback: types.CallbackQuery, session: AsyncSession):
    """Показывает детали заказа."""
    order_id = int(callback.data.split("_")[3])
    result = await session.execute(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    order = result.scalars().first()

    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    status_name = STATUS_NAMES.get(order.status, order.status)
    text = (
        f"<b>Заказ #{order.id}</b>\n"
        f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        f"📌 Статус: {status_name}\n\n"
        f"👤 {order.customer_name}\n"
        f"📞 {order.customer_phone}\n"
        f"🚚 Доставка: {order.delivery_method_name or 'Не выбрана'}\n"
        f"📍 Адрес: {order.delivery_address or 'Самовывоз'}\n"
        f"💬 {order.comment or 'Без комментария'}\n\n"
        f"<b>Товары:</b>\n"
    )
    for item in order.items:
        text += f"• {item.product_name} — {item.quantity} шт. × {item.price} ₽\n"
    text += f"\n💰 <b>Итого: {order.total_amount} ₽</b>"

    keyboard = get_order_status_keyboard(order.id, order.status)
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_order_setstatus_"))
async def admin_order_set_status(callback: types.CallbackQuery, session: AsyncSession):
    """Меняет статус заказа и уведомляет покупателя."""
    parts = callback.data.split("_")
    order_id = int(parts[3])
    new_status = parts[4]

    result = await session.execute(select(Order).where(Order.id == order_id))
    order = result.scalars().first()
    if not order:
        await callback.answer("Заказ не найден", show_alert=True)
        return

    order.status = new_status
    await session.commit()

    # Уведомляем покупателя
    user_result = await session.execute(select(User).where(User.id == order.user_id))
    user = user_result.scalars().first()

    if user:
        acc_result = await session.execute(
            select(PlatformAccount).where(
                PlatformAccount.user_id == user.id,
                PlatformAccount.platform == "telegram"
            )
        )
        acc = acc_result.scalars().first()
        if acc:
            try:
                status_text = STATUS_NAMES.get(new_status, new_status)
                await callback.bot.send_message(
                    chat_id=int(acc.platform_id),
                    text=f"📦 Статус вашего заказа #{order.id} изменён на: <b>{status_text}</b>"
                )
            except Exception as e:
                print(f"Не удалось уведомить покупателя: {e}")

    await callback.answer(f"Статус изменён на {STATUS_NAMES.get(new_status, new_status)}", show_alert=True)
    
    await admin_orders_list(callback, session)


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: types.CallbackQuery):
    """Возврат в главное меню админа."""
    await callback.message.edit_text(
        "<b>Панель управления</b>\n\nВыберите раздел:",
        reply_markup=get_admin_main_menu()
    )
    await callback.answer()