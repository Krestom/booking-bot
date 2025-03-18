from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import logging
import os
from dotenv import load_dotenv
import random

# Загрузка переменных окружения
load_dotenv()
CHROME_DRIVER_PATH = os.getenv('CHROME_DRIVER_PATH')

def generate_booking_url(booking_data):
    """
    Формирует ссылку для бронирования и пытается записать пользователя.
    Сначала пытается записаться в выбранный класс.
    Если не удалось – перебирает 3 случайных альтернативных класса из словаря.
    """
    logging.info(f"Попытка бронирования: {booking_data}")

    class_type_1 = '18249588'
    class_type_2 = '18505562'

    # Обновлённый словарь классов без класса "anyone"
    classes = {
        '0207': 3673411, '0209': 3712681, '0210': 3712682, '0211': 3712684, '0212': 3712686,
        '0213': 3712689, '0214': 3712690, '0215': 3712692, '0216': 3712693,
        '0218': 3712694, '0219': 3712695, '0220': 3712696, '0221': 3712697,
        '0222': 3712698, '0223': 3712699, '0224': 3712700, '0225': 3712701,
        '0226': 3712702, '0227': 3712703, '0228': 3712705, '0229': 3712707, '0230': 3712710,
        '0231': 3712713, '0232': 3712715, '0233': 3712716
    }

    # Форматирование даты и времени
    dt = datetime.strptime(booking_data["date"], "%Y-%d-%m")
    formatted_date = dt.strftime("%y%d%m")
    dt_time_obj = datetime.strptime(booking_data["time"], "%H:%M")
    formatted_time = dt_time_obj.strftime("%H%M")

    class_type = class_type_1 if booking_data["duration"] == '1 час' else class_type_2
    desired_class = booking_data["class_name"]

    def attempt_booking(selected_class):
        class_id = classes.get(selected_class)
        if not class_id:
            logging.error(f"Класс {selected_class} не найден в словаре доступных классов.")
            return False, None
        url = f'https://n1340880.yclients.com/company/1219726/create-record/record?o=m{class_id}s{class_type}d{formatted_date}{formatted_time}'
        logging.info(f"Попытка бронирования для класса {selected_class} по ссылке {url}")

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

            inputs = {
                'surname_input': booking_data["last_name"],
                'name_input': booking_data["first_name"],
                'phone_input': booking_data["phone"]
            }

            for field, value in inputs.items():
                input_element = wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, f'input[data-locator="{field}"]')
                ))
                input_element.send_keys(value)

            comment_input = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'textarea[data-locator="comment_input"]')
            ))
            comment_input.send_keys(booking_data['room_number'])

            register_button = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[text()='Записаться']")
            ))
            register_button.click()

            success_message = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div[data-locator="created_booking_page_title"]')
            ))
            if success_message.text == "Вы записаны":
                logging.info(f"✅ Успешное бронирование в класс {selected_class} по ссылке {url}")
                return True, selected_class
            else:
                logging.error(f"❌ Не удалось подтвердить бронирование в класс {selected_class}.Текст сообщения: {success_message.text}")
        except Exception as e:
            logging.error(f"❌ Ошибка бронирования для класса {selected_class}: {e}")
            logging.error(f"Ссылка ошибки: {url}")
        finally:
            driver.quit()
        return False, None

    # 1. Пытаемся записать в выбранный пользователем класс
    success, booked_class = attempt_booking(desired_class)
    if success:
        return True, booked_class

    # 2. Если не удалось, выбираем 3 случайных альтернативы из остальных классов
    alternative_classes = [cl for cl in classes.keys() if cl != desired_class]
    random.shuffle(alternative_classes)
    attempts = alternative_classes[:3]
    for alt_class in attempts:
        success, booked_class = attempt_booking(alt_class)
        if success:
            return True, alt_class

    logging.error("❌ Бронирование не удалось ни для выбранного класса, ни для альтернатив.")
    return False, None