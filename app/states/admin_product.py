from aiogram.fsm.state import State, StatesGroup


class ProductCreateState(StatesGroup):
    name = State()
    description = State()
    photo = State()
    price = State()
    stock = State()
    category = State()
