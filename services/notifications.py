from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import ADMIN_ID
from database.models import Order

STATUS_NAMES = {
    "new": "🆕 Новый",
    "pending_payment": "⏳ Ожидает оплаты",
    "pending": "⏳ Ожидает оплаты",
    "paid": "✅ Оплачен",
    "processing": "📦 В обработке",
    "shipped": "🚚 Отправлен",
    "completed": "🏁 Выполнен",
    "cancelled": "❌ Отменён",
}

async def notify_admin_new_order(bot: Bot, order: Order, items: list):
    if not ADMIN_ID:
        print("ADMIN_ID не задан, уведомление не отправлено.")
        return

    status_text = STATUS_NAMES.get(order.status, order.status)
    text = (
        f"🆕 <b>Новый заказ #{order.id}</b>\n"
        f"📌 Статус: {status_text}\n\n"
        f"👤 Имя: {order.customer_name}\n"
        f"📞 Телефон: {order.customer_phone}\n"
        f"🚚 Доставка: {order.delivery_method_name or 'Не выбрана'}\n"
        f"📍 Адрес: {order.delivery_address or 'Самовывоз'}\n"
        f"💬 Комментарий: {order.comment or 'Нет'}\n\n"
        f"<b>Товары:</b>\n"
    )
    for item in items:
        text += f"• {item.product_name} — {item.quantity} шт. × {item.price} ₽\n"
    
    text += f"\n💰 <b>Итого: {order.total_amount} ₽</b>"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Открыть заказ", callback_data=f"admin_order_view_{order.id}")],
        [InlineKeyboardButton(text="⏳ Ожидает оплаты", callback_data=f"admin_order_setstatus_{order.id}_pending_payment")],
        [InlineKeyboardButton(text="✅ Оплачен", callback_data=f"admin_order_setstatus_{order.id}_paid")],
        [InlineKeyboardButton(text="📦 В обработке", callback_data=f"admin_order_setstatus_{order.id}_processing")],
        [InlineKeyboardButton(text="🚚 Отправлен", callback_data=f"admin_order_setstatus_{order.id}_shipped")],
        [InlineKeyboardButton(text="🏁 Выполнен", callback_data=f"admin_order_setstatus_{order.id}_completed")],
        [InlineKeyboardButton(text="❌ Отменён", callback_data=f"admin_order_setstatus_{order.id}_cancelled")],
    ])

    try:
        await bot.send_message(chat_id=ADMIN_ID, text=text, reply_markup=keyboard)
    except Exception as e:
        print(f"Ошибка отправки уведомления админу: {e}")