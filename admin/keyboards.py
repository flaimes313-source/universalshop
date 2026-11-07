from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    ReplyKeyboardMarkup, KeyboardButton
)
from database.models import Category

# --- Клавиатуры для добавления товара ---

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

def get_skip_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой пропуска (для необязательных полей)."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="⏩ Пропустить")], [KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

def get_categories_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    """Клавиатура для выбора категории (при добавлении товара)."""
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(text=cat.name, callback_data=f"cat_{cat.id}")])
    keyboard.append([InlineKeyboardButton(text="Без категории", callback_data="cat_none")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения добавления товара."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Сохранить", callback_data="product_save")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="product_cancel")]
        ]
    )

# --- Клавиатуры для управления категориями (Админка) ---

def get_categories_admin_keyboard(categories: list[Category]) -> InlineKeyboardMarkup:
    """Клавиатура со списком всех категорий для админа."""
    keyboard = []
    for cat in categories:
        status = "✅" if cat.is_active else "❌"
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status} {cat.name}", 
                callback_data=f"admin_cat_view_{cat.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton(text="➕ Добавить категорию", callback_data="admin_cat_add")])
    keyboard.append([InlineKeyboardButton(text="🔙 Назад в админ-меню", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_category_actions_keyboard(cat_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с конкретной категорией."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Переименовать", callback_data=f"admin_cat_edit_{cat_id}")],
        [InlineKeyboardButton(text="🔄 Скрыть/Показать", callback_data=f"admin_cat_toggle_{cat_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_cat_del_{cat_id}")],
        [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="admin_categories")]
    ])