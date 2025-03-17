# states.py
from aiogram.fsm.state import StatesGroup, State

class BookingState(StatesGroup):
    date = State()
    duration = State()
    time = State()
    class_name = State()
    last_name = State()
    first_name = State()
    phone = State()
    room_number = State()
    confirm = State()