from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Генерирует главное меню администратора (Inline-кнопки по 2 в ряд)."""
    # Список кнопок
    buttons = [
        ("📦 Товары и каталог", "admin_products"),
        ("📦 Управление товарами", "admin_products_manage"),
        ("📁 Категории", "admin_categories"),
        ("📋 Заказы", "admin_orders"),
        ("💳 Оплата", "admin_payments"),
        ("🚚 Доставка", "admin_delivery"),
        ("👥 Клиенты", "admin_customers"),
        ("⚙️ Настройки", "admin_settings"),
        ("📊 Статистика", "admin_statistics"),
        ("📈 Аналитика", "admin_analytics"),
        ("👑 Администраторы", "admin_admins"),
    ]
    
    # Группируем по 2
    keyboard = []
    row = []
    for text, callback in buttons:
        row.append(InlineKeyboardButton(text=text, callback_data=callback))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)  # добавляем остаток
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)