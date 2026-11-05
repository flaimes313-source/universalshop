from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database.models import Category

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
    """Клавиатура для выбора категории."""
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