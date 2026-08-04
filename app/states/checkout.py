from aiogram.fsm.state import State, StatesGroup


class CheckoutState(StatesGroup):
    name = State()
    lastname = State()
    surname = State()
    phone = State()
    address = State()
    delivery = State()
    confirm = State()
