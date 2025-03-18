import asyncio
import logging
from datetime import datetime, time as dt_time, timedelta
from aiogram import Bot
from app.database import get_today_bookings, update_booking_status
from app.url_generator import generate_booking_url
import os
from dotenv import load_dotenv
import random

# Дополнительные импорты для работы с Selenium при проверке страницы
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver

# Загрузка переменных окружения
load_dotenv(dotenv_path="./.env")
bot = Bot(token=os.getenv('TG_TOKEN'))
CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH')

# Ограничение на 5 одновременных бронирований
semaphore = asyncio.Semaphore(5)

def parse_time(time_str):
    hours, minutes, seconds = map(int, time_str.split(':'))
    return dt_time(hour=hours, minute=minutes, second=seconds)

START_TIME = parse_time(os.getenv('START_TIME'))
END_TIME = parse_time(os.getenv('END_TIME'))

async def process_booking(booking):
    """
    Обрабатывает бронирование одной заявки с учетом ограничения по потокам.
    """
    async with semaphore:
        booking_id, user_id, date, duration, time_slot, class_name, last_name, first_name, phone, room_number, status = booking

        booking_data = {
            "date": date,
            "duration": duration,
            "time": time_slot,
            "class_name": class_name,
            "last_name": last_name,
            "first_name": first_name,
            "phone": phone,
            "room_number": room_number
        }

        logging.info(f"🔄 Начало бронирования заявки {booking_id} для пользователя {user_id}")
        success, final_class = await asyncio.to_thread(generate_booking_url, booking_data)

        if success:
            update_booking_status(booking_id, "success")
            if final_class == class_name:
                await bot.send_message(user_id, "✅ Ваше занятие успешно забронировано!")
            else:
                await bot.send_message(user_id, f"⚠️ Ваш класс был занят, вас записали в {final_class}.")
        else:
            update_booking_status(booking_id, "failed")
            await bot.send_message(user_id, "❌ Не удалось забронировать занятие.", disable_notification=True)

async def process_bookings():
    """
    Запускает бронирование для всех заявок на текущий день с ограничением по потокам.
    """
    bookings = get_today_bookings()
    if bookings:
        tasks = [process_booking(booking) for booking in bookings]
        await asyncio.gather(*tasks)

def check_booking_page(booking_data):
    """
    Проверяет, доступна ли страница для бронирования.
    Открывает URL для выбранного класса и ищет наличие поля ввода (surname_input).
    Если элемент найден – возвращает True.
    """
    class_type_1 = '18249588'
    class_type_2 = '18505562'
    # Словарь классов без "anyone"
    classes = {
        '0207': 3673411, '0209': 3712681, '0210': 3712682, '0211': 3712684, '0212': 3712686,
        '0213': 3712689, '0214': 3712690, '0215': 3712692, '0216': 3712693,
        '0218': 3712694, '0219': 3712695, '0220': 3712696, '0221': 3712697,
        '0222': 3712698, '0223': 3712699, '0224': 3712700, '0225': 3712701,
        '0226': 3712702, '0227': 3712703, '0228': 3712705, '0229': 3712707, '0230': 3712710,
        '0231': 3712713, '0232': 3712715, '0233': 3712716
    }
    try:
        dt_obj = datetime.strptime(booking_data["date"], "%Y-%d-%m")
    except Exception as e:
        logging.error(f"Ошибка при разборе даты: {e}")
        return False
    formatted_date = dt_obj.strftime("%y%d%m")

    try:
        dt_time_obj = datetime.strptime(booking_data["time"], "%H:%M")
    except Exception as e:
        logging.error(f"Ошибка при разборе времени: {e}")
        return False
    formatted_time = dt_time_obj.strftime("%H%M")

    class_type = class_type_1 if booking_data["duration"] == '1 час' else class_type_2
    desired_class = booking_data["class_name"]
    class_id = classes.get(desired_class)
    if not class_id:
         logging.error(f"Класс {desired_class} не найден в словаре доступных классов.")
         return False
    url = f'https://n1340880.yclients.com/company/1219726/create-record/record?o=m{class_id}s{class_type}d{formatted_date}{formatted_time}'
    logging.info(f"Проверка страницы бронирования для класса {desired_class} по ссылке {url}")

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-logging")
    options.add_experimental_option("excludeSwitches", ['enable-logging', 'enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)

    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        driver.get(url)
        wait = WebDriverWait(driver, 5)
        # Пытаемся найти поле ввода фамилии – одного из индикаторов, что страница готова к записи
        input_element = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'input[data-locator="surname_input"]')
        ))
        input_element_1 = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'input[data-locator="name_input"]')
        ))
        input_element_2 = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, 'input[data-locator="phone_input"]')
        ))
        if input_element or input_element_1 or input_element_2:
            logging.info("Страница бронирования доступна для записи.")
            return True
    except Exception as e:
        logging.info(f"Страница бронирования еще не доступна")
    finally:
        driver.quit()
    return False

async def scheduler():
    """
    Основной цикл планировщика:
    - Ждёт наступления времени START_TIME, указанного в .env.
    - После наступления времени каждые 30 секунд случайным образом выбирает заявку из сегодняшних,
      формирует URL и проверяет, доступна ли страница бронирования.
    - Как только страница обнаружена (найден хотя бы один input),
      запускается процесс бронирования для всех заявок.
    - После завершения цикл переходит к следующему дню.
    """
    while True:
        now = datetime.now().time()
        today = datetime.today()
        next_start = datetime.combine(today, START_TIME)
        if now >= START_TIME:
            next_start += timedelta(days=1)
        sleep_time = (next_start - datetime.now()).total_seconds()
        logging.info(f"Ожидание до начала бронирования: {next_start.strftime('%Y-%m-%d %H:%M:%S')} ({sleep_time} секунд)")
        await asyncio.sleep(sleep_time)

        logging.info("Начало проверки доступности страницы бронирования каждые 30 секунд.")
        booking_page_available = False
        while not booking_page_available:
            bookings = get_today_bookings()
            if not bookings:
                logging.info("Нет заявок на бронирование сегодня.")
                await asyncio.sleep(15)
                continue
            # Выбираем случайную заявку для проверки
            random_booking = random.choice(bookings)
            booking_data = {
                "date": random_booking[2],
                "duration": random_booking[3],
                "time": random_booking[4],
                "class_name": random_booking[5],
                "last_name": random_booking[6],
                "first_name": random_booking[7],
                "phone": random_booking[8],
                "room_number": random_booking[9]
            }
            logging.info(f"Проверка доступности страницы для заявки id {random_booking[0]}")
            logging.info(f'Данные: {booking_data}')
            booking_page_available = await asyncio.to_thread(check_booking_page, booking_data)
            if booking_page_available:
                logging.info("Страница бронирования обнаружена, запускаем процесс бронирования для всех заявок.")
                await process_bookings()
                break
            else:
                logging.info("Страница бронирования ещё не доступна, повторная проверка через 30 секунд.")
                await asyncio.sleep(15)