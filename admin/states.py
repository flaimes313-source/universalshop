from aiogram.fsm.state import State, StatesGroup

class AddProductStates(StatesGroup):
    """Состояния для добавления товара."""
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_old_price = State()
    waiting_for_photo = State()
    waiting_for_category = State()
    waiting_for_stock = State()
    waiting_for_confirm = State()

class CategoryStates(StatesGroup):
    """Состояния для управления категориями."""
    waiting_for_name = State()
    waiting_for_edit_name = State()

class SettingsStates(StatesGroup):
    """Состояния для изменения настроек магазина."""
    waiting_for_value = State()

class StatisticsStates(StatesGroup):
    """Состояния для просмотра статистики."""
    waiting_for_period = State()