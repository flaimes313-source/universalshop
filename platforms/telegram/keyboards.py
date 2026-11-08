from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database.models import MenuItem
from config import ADMIN_ID

def get_main_menu_keyboard(menu_items: list[MenuItem], is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Создает главное меню из списка кнопок, полученных из БД (по 2 в ряд)."""
    keyboard = []
    row = []
    
    for item in menu_items:
        row.append(KeyboardButton(text=item.title))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if is_admin:
        row.append(KeyboardButton(text="⚙️ Админ-панель"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    if not keyboard:
        keyboard = [[KeyboardButton(text="Каталог")]]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

def get_cart_keyboard(cart_items: list) -> InlineKeyboardMarkup:
    """Клавиатура для управления корзиной."""
    keyboard = []
    for item in cart_items:
        item_total = item.product.price * item.quantity if item.product else 0
        button_text = f"{item.product.name if item.product else 'Товар'} ({item.quantity} шт.) = {item_total} ₽"
        
        keyboard.append([
            InlineKeyboardButton(text="➖", callback_data=f"cart_minus_{item.id}"),
            InlineKeyboardButton(text=button_text, callback_data="noop"),
            InlineKeyboardButton(text="➕", callback_data=f"cart_plus_{item.id}"),
            InlineKeyboardButton(text="❌", callback_data=f"cart_del_{item.id}")
        ])
    
    keyboard.append([InlineKeyboardButton(text="🗑 Очистить корзину", callback_data="cart_clear")])
    keyboard.append([InlineKeyboardButton(text="✅ Оформить заказ", callback_data="cart_checkout")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)