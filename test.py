import asyncio
import logging
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("test.log", mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Загрузка переменных окружения
load_dotenv(dotenv_path=os.path.join(os.pardir, '.env'))
CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH')

# Мок-данные для бронирований
def generate_mock_bookings():
    today = datetime.today()
    bookings = []
    for i in range(3):  # Генерируем 3 бронирования для теста
        booking_data = {
            "date": (today + timedelta(days=i)).strftime("%Y-%d-%m"),
            "duration": "1 час" if i % 2 == 0 else "2 часа",
            "time": f"{10 + i}:00",
            "class_name": f"02{i:02d}",
            "last_name": f"Фамилия{i}",
            "first_name": f"Имя{i}",
            "phone": f"900123456{i}",
            "room_number": f"Комната {i}"
        }
        bookings.append(booking_data)
    return bookings

# Функция для бронирования (полностью повторяет логику вашего скрипта)
def generate_booking_url(booking_data):
    logging.info(f"Попытка бронирования: {booking_data}")

    class_type_1 = '18249588'
    class_type_2 = '18505562'

    classes = {
        '0207': 3673411, '0209': 3712681, '0210': 3712682, '0212': 3712686,
        '0213': 3712689, '0214': 3712690, '0215': 3712692, '0216': 3712693,
        '0218': 3712694, '0219': 3712695, '0220': 3712696, '0221': 3712697,
        '0222': 3712698, '0223': 3712699, '0224': 3712700, '0225': 3712701,
        '0226': 3712702, '0227': 3712703, '0229': 3712707, '0230': 3712710,
        '0231': 3712713, '0232': 3712715, '0233': 3712716, 'anyone': 'm-1'
    }

    dt = datetime.strptime(booking_data["date"], "%Y-%d-%m")
    formatted_date = dt.strftime("%y%d%m")

    dt_time_obj = datetime.strptime(booking_data["time"], "%H:%M")
    formatted_time = dt_time_obj.strftime("%H%M")

    class_type = class_type_1 if booking_data["duration"] == '1 час' else class_type_2
    selected_class = booking_data["class_name"]

    # Предварительная проверка наличия свободного времени
    pre_check_url = f'https://n1340880.yclients.com/company/1219726/personal/select-time?o=s{class_type}'

    # Основной цикл бронирования
    for attempt in range(2):  # Две попытки: сначала в выбранный класс, потом в "anyone"
        class_id = classes.get(selected_class, 'm-1')
        url = f'https://n1340880.yclients.com/company/1219726/create-record/record?o=m{class_id}s{class_type}d{formatted_date}{formatted_time}'

        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Отключаем логи chromedriver
        service = Service(CHROME_DRIVER_PATH, log_output=os.devnull)
        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.get(url)
            wait = WebDriverWait(driver, 3)

            inputs = {
                'surname_input': booking_data["last_name"],
                'name_input': booking_data["first_name"],
                'phone_input': booking_data["phone"]
            }

            for field, value in inputs.items():
                input_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, f'input[data-locator="{field}"]')))
                input_element.send_keys(value)

            comment_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[data-locator="comment_input"]')))
            comment_input.send_keys(booking_data['room_number'])

            register_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='Записаться']")))
            register_button.click()

            success_message = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-locator="created_booking_page_title"]')))
            if success_message.text == "Вы записаны":
                logging.info(f"Успешное бронирование в класс {selected_class} по ссылке {url}")
                return True, selected_class  # Бронирование успешно

        except Exception as e:
            # logging.error(f"Ошибка бронирования для класса {selected_class}: {e}")
            logging.error(f'Ссылка ошибки {url}')

        finally:
            driver.quit()

        # Если первая попытка не удалась, пробуем класс "anyone"
        if attempt == 0:
            logging.info(f"Попытка забронировать класс 'anyone' вместо {selected_class}")
            selected_class = "anyone"

    logging.error(f"Обе попытки бронирования не удались. Финальная ссылка {url}")
    return False, None  # Обе попытки не удались

# Основная функция для параллельного бронирования
async def process_bookings():
    mock_bookings = generate_mock_bookings()
    tasks = [asyncio.to_thread(generate_booking_url, booking) for booking in mock_bookings]
    results = await asyncio.gather(*tasks)
    logging.info(f"Результаты бронирований: {results}")

async def main():
    logging.info("Запуск тестового скрипта для параллельного бронирования")
    await process_bookings()
    logging.info("Тестовый скрипт завершен")

if __name__ == "__main__":
    asyncio.run(main())