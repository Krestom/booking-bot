from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta

# --- Клавиатура выбора даты ---
async def date_keyboard():
    today = datetime.today()
    dates = [(today + timedelta(days=i)).strftime('%Y-%d-%m') for i in range(4)]  # Формат yyyy-dd-mm
    keyboard = InlineKeyboardBuilder()
    for date in dates:
        keyboard.add(InlineKeyboardButton(text=date, callback_data=f'date_{date}'))
    return keyboard.adjust(1).as_markup()

# --- Клавиатура выбора продолжительности ---
async def duration_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='1 час', callback_data='duration_1_hour'),
         InlineKeyboardButton(text='2 часа', callback_data='duration_2_hours')],
        [InlineKeyboardButton(text='Назад', callback_data='go_back_date')]
    ])

# --- Клавиатура выбора времени ---
async def time_keyboard():
    keyboard = InlineKeyboardBuilder()
    for hour in range(7, 24):  # От 7:00 до 23:00
        keyboard.add(InlineKeyboardButton(text=f"{hour}:00", callback_data=f"time_{hour}:00"))
    keyboard.row(InlineKeyboardButton(text='Назад', callback_data='go_back_duration'))
    return keyboard.as_markup()

# --- Клавиатура выбора класса ---
async def classes_builder():
    classes = ["0207", "0209", "0210", "0211",
               "0212", "0213", "0214", "0215", "0216",
               "0219", "0220", "0226", "0228"]
    keyboard = InlineKeyboardBuilder()
    for cl in classes:
        keyboard.add(InlineKeyboardButton(text=cl, callback_data=f'class_{cl}'))
    keyboard.row(InlineKeyboardButton(text='Назад', callback_data='go_back_time'))
    return keyboard.as_markup()

# --- Клавиатура подтверждения ---
async def confirmation_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✅ Подтверждаю', callback_data='confirm_booking')],
        [InlineKeyboardButton(text='Назад', callback_data='go_back_room')]
    ])

# --- Клавиатура отмены заявки ---
async def cancel_booking_keyboard(booking_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить заявку", callback_data=f"cancel_booking_{booking_id}")]
    ])

# --- Клавиатура списка заявок ---
async def bookings_list_keyboard(bookings):
    keyboard = InlineKeyboardBuilder()
    for booking_id, date, time, class_name in bookings:
        keyboard.add(InlineKeyboardButton(
            text=f"{date}, {time}, {class_name}",
            callback_data=f"cancel_booking_{booking_id}"
        ))
    return keyboard.adjust(1).as_markup()

# --- Универсальная клавиатура "Назад" ---
async def back_keyboard(callback_data: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Назад", callback_data=callback_data)]
    ])

# --- Клавиатура "Начать заново" ---
async def restart_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Начать заново", callback_data="restart_booking")]
    ])