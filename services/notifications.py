from aiogram import Bot
from config import ADMIN_ID
from database.models import Order

async def notify_admin_new_order(bot: Bot, order: Order, items: list):
    """
    Отправляет уведомление администратору о новом заказе.
    items — список OrderItem для формирования состава заказа.
    """
    if not ADMIN_ID:
        print("ADMIN_ID не задан, уведомление не отправлено.")
        return

    text = (
        f"🆕 <b>Новый заказ #{order.id}</b>\n\n"
        f"👤 Имя: {order.customer_name}\n"
        f"📞 Телефон: {order.customer_phone}\n"
        f"🚚 Адрес: {order.delivery_address or 'Самовывоз'}\n"
        f"💬 Комментарий: {order.comment or 'Нет'}\n\n"
        f"<b>Товары:</b>\n"
    )
    for item in items:
        text += f"• {item.product_name} — {item.quantity} шт. × {item.price} ₽\n"
    
    text += f"\n💰 <b>Итого: {order.total_amount} ₽</b>"

    try:
        await bot.send_message(chat_id=ADMIN_ID, text=text)
    except Exception as e:
        print(f"Ошибка отправки уведомления админу: {e}")