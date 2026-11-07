from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Генерирует главное меню администратора (Inline-кнопки)."""
    keyboard = [
        [InlineKeyboardButton(text="📦 Товары и каталог", callback_data="admin_products")],
        [InlineKeyboardButton(text="📁 Категории", callback_data="admin_categories")],
        [InlineKeyboardButton(text="📋 Заказы", callback_data="admin_orders")],
        [InlineKeyboardButton(text="💳 Оплата", callback_data="admin_payments")],
        [InlineKeyboardButton(text="🚚 Доставка", callback_data="admin_delivery")],
        [InlineKeyboardButton(text="👥 Клиенты", callback_data="admin_customers")],
        [InlineKeyboardButton(text="⚙️ Настройки магазина", callback_data="admin_settings")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_statistics")],
        [InlineKeyboardButton(text="📈 Аналитика", callback_data="admin_analytics")],  # <-- Новая кнопка
        [InlineKeyboardButton(text="👑 Администраторы", callback_data="admin_admins")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)