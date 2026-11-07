from aiogram.fsm.state import State, StatesGroup

class AddProductStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_old_price = State()
    waiting_for_photo = State()
    waiting_for_category = State()
    waiting_for_stock = State()
    waiting_for_confirm = State()

class CategoryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_edit_name = State()

class SettingsStates(StatesGroup):
    waiting_for_value = State()

class StatisticsStates(StatesGroup):
    waiting_for_period = State()

class DeliveryStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_price = State()

class EditProductStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_price = State()
    waiting_for_stock = State()