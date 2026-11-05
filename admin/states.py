from aiogram.fsm.state import State, StatesGroup

class AddProductStates(StatesGroup):
    """Состояния для добавления товара."""
    waiting_for_name = State()        # Ожидание названия
    waiting_for_description = State() # Ожидание описания
    waiting_for_price = State()       # Ожидание цены
    waiting_for_old_price = State()   # Ожидание старой цены (для скидки)
    waiting_for_photo = State()       # Ожидание фотографии
    waiting_for_category = State()    # Выбор категории
    waiting_for_stock = State()       # Ожидание остатка
    waiting_for_confirm = State()     # Подтверждение сохранения