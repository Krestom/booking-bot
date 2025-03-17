from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from app.database import save_booking, is_time_slot_taken, get_user_bookings, cancel_booking
from app.states import BookingState
import app.keyboards as kb
from aiogram.types import InlineKeyboardMarkup

router = Router()

# --- Команда /start ---
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.set_state(BookingState.date)
    await message.answer("Привет! Выберите дату занятия:", reply_markup=await kb.date_keyboard())

# --- Выбор даты ---
@router.callback_query(BookingState.date, F.data.startswith('date_'))
async def date_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(date=callback.data.split('_')[1])
    await state.set_state(BookingState.duration)
    await callback.message.edit_text("Выберите продолжительность:", reply_markup=await kb.duration_keyboard())

# --- Исправлена обработка кнопки "Назад" при выборе длительности ---
@router.callback_query(BookingState.duration, F.data == "go_back_date")
async def go_back_to_date(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingState.date)
    await callback.message.edit_text("Выберите дату занятия:", reply_markup=await kb.date_keyboard())

# --- Выбор продолжительности ---
@router.callback_query(BookingState.duration, F.data.startswith('duration_'))
async def duration_handler(callback: CallbackQuery, state: FSMContext):
    duration = "1 час" if "1_hour" in callback.data else "2 часа"
    await state.update_data(duration=duration)
    await state.set_state(BookingState.time)
    await callback.message.edit_text("Выберите время занятия:", reply_markup=await kb.time_keyboard())

# --- Обработка кнопки "Назад" при выборе времени ---
@router.callback_query(BookingState.time, F.data == "go_back_duration")
async def go_back_to_duration(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingState.duration)
    await callback.message.edit_text("Выберите продолжительность:", reply_markup=await kb.duration_keyboard())

# --- Выбор времени ---
@router.callback_query(BookingState.time, F.data.startswith('time_'))
async def time_handler(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_time = callback.data.split('_')[1]
    if is_time_slot_taken(data["date"], selected_time, data.get("class_name", "anyone")):
        await callback.message.edit_text(
            "❌ Это время уже занято! Попробуйте выбрать другое.",
            reply_markup=await kb.restart_keyboard()
        )
        return
    await state.update_data(time=selected_time)
    await state.set_state(BookingState.class_name)
    await callback.message.edit_text("Выберите класс:", reply_markup=await kb.classes_builder())

# --- Обработка кнопки "Назад" при выборе класса ---
@router.callback_query(BookingState.class_name, F.data == "go_back_time")
async def go_back_to_time(callback: CallbackQuery, state: FSMContext):
    await state.set_state(BookingState.time)
    await callback.message.edit_text("Выберите время занятия:", reply_markup=await kb.time_keyboard())

# --- Выбор класса ---
@router.callback_query(BookingState.class_name, F.data.startswith('class_'))
async def class_handler(callback: CallbackQuery, state: FSMContext):
    await state.update_data(class_name=callback.data.split('_')[1])
    await state.set_state(BookingState.last_name)
    await callback.message.answer("Введите вашу фамилию:", reply_markup=await kb.back_keyboard("go_back_class"))

# --- Ввод фамилии ---
@router.message(BookingState.last_name)
async def last_name_handler(message: Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await state.set_state(BookingState.first_name)
    await message.answer("Введите ваше имя:", reply_markup=await kb.back_keyboard("go_back_last_name"))

# --- Ввод имени ---
@router.message(BookingState.first_name)
async def first_name_handler(message: Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await state.set_state(BookingState.phone)
    await message.answer("Введите ваш номер телефона (без кода страны, начните с цифры 9️⃣):", reply_markup=await kb.back_keyboard("go_back_first_name"))

# --- Ввод номера телефона ---
@router.message(BookingState.phone)
async def phone_handler(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(BookingState.room_number)
    await message.answer("Введите номер вашей комнаты и корпуса:", reply_markup=await kb.back_keyboard("go_back_phone"))

# --- Ввод номера комнаты ---
@router.message(BookingState.room_number)
async def room_number_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    data['user_id'] = message.from_user.id
    data['room_number'] = message.text  
    await state.update_data(data)
    confirmation_text = (
        f"✅ Проверьте данные:\n"
        f"📅 Дата: {data['date']}\n"
        f"⏳ Длительность: {data['duration']}\n"
        f"⏰ Время: {data['time']}\n"
        f"🏫 Класс: {data['class_name']}\n"
        f"👤 Имя: {data['first_name']} {data['last_name']}\n"
        f"📞 Телефон: {data['phone']}\n"
        f"🚪 Комната: {data['room_number']}\n"
    )
    await message.answer(confirmation_text, reply_markup=await kb.confirmation_keyboard())

# --- Подтверждение бронирования ---
@router.callback_query(F.data == 'confirm_booking')
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if 'user_id' not in data:
        data['user_id'] = callback.from_user.id
    if 'room_number' not in data:
        await callback.message.edit_text("❌ Ошибка: номер комнаты отсутствует. Введите его снова.")
        await state.set_state(BookingState.room_number)
        return
    success = save_booking(data)
    if not success:
        await callback.message.edit_text(
            "❌ Это время уже занято! Попробуйте выбрать другое.",
            reply_markup=await kb.restart_keyboard()
        )
        return
    await state.clear()
    await callback.message.edit_text("✅ Данные сохранены. Ваша заявка получена.")

# --- Кнопка "Начать заново" ---
@router.callback_query(F.data == 'restart_booking')
async def restart_booking(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await cmd_start(callback.message, state)

# --- Обработка кнопки "Назад" во всех состояниях ---
@router.callback_query(F.data.startswith('go_back_'))
async def go_back_handler(callback: CallbackQuery, state: FSMContext):
    back_step = {
        "go_back_date": (BookingState.date, "Выберите дату занятия:", kb.date_keyboard),
        "go_back_duration": (BookingState.duration, "Выберите продолжительность:", kb.duration_keyboard),
        "go_back_time": (BookingState.time, "Выберите время занятия:", kb.time_keyboard),
        "go_back_class": (BookingState.class_name, "Выберите класс:", kb.classes_builder),
        "go_back_last_name": (BookingState.last_name, "Введите вашу фамилию:", lambda: kb.back_keyboard("go_back_class")),
        "go_back_first_name": (BookingState.first_name, "Введите ваше имя:", lambda: kb.back_keyboard("go_back_last_name")),
        "go_back_phone": (BookingState.phone, "Введите ваш номер телефона:", lambda: kb.back_keyboard("go_back_first_name")),
        "go_back_room": (BookingState.room_number, "Введите номер вашей комнаты и корпуса:", lambda: kb.back_keyboard("go_back_phone")),
    }
    step = callback.data
    if step in back_step:
        state_to_set, message_text, keyboard_func = back_step[step]
        await state.set_state(state_to_set)
        if isinstance(await keyboard_func(), InlineKeyboardMarkup):
            await callback.message.edit_text(message_text, reply_markup=await keyboard_func())
        else:
            await callback.message.answer(message_text, reply_markup=await keyboard_func())

# --- Команда /my_bookings для просмотра активных заявок ---
@router.message(Command("my_bookings"))
async def my_bookings(message: Message):
    bookings = get_user_bookings(message.from_user.id)
    if not bookings:
        await message.answer("У вас нет активных заявок.")
        return
    if len(bookings) == 1:
        booking_id, date, time, class_name = bookings[0]
        await message.answer(
            f"📅 {date}, ⏰ {time}, 🏫 {class_name}\nХотите отменить?",
            reply_markup=await kb.cancel_booking_keyboard(booking_id)
        )
    else:
        await message.answer("Выберите заявку для отмены:", reply_markup=await kb.bookings_list_keyboard(bookings))

# --- Обработка отмены заявки ---
@router.callback_query(F.data.startswith("cancel_booking_"))
async def cancel_booking_handler(callback: CallbackQuery):
    booking_id = int(callback.data.split("_")[2])
    cancel_booking(booking_id)
    await callback.message.edit_text("✅ Ваша заявка была отменена.")