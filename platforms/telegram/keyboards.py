from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database.models import MenuItem

def get_main_menu_keyboard(menu_items: list[MenuItem]) -> ReplyKeyboardMarkup:
    """
    Создает главное меню из списка кнопок, полученных из БД.
    Кнопки располагаются по 2 в ряд.
    """
    keyboard = []
    row = []
    
    for item in menu_items:
        row.append(KeyboardButton(text=item.title))
        if len(row) == 2:  # По 2 кнопки в ряд
            keyboard.append(row)
            row = []
            
    if row:  # Добавляем остаток, если количество кнопок нечетное
        keyboard.append(row)

    # Если меню пустое (например, админ удалил все кнопки), добавляем дефолтную
    if not keyboard:
        keyboard = [[KeyboardButton(text="Каталог")]]

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )