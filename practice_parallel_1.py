import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Путь к chromedriver
CHROME_DRIVER_PATH = "chromedriver.exe"  # Укажите свой путь к chromedriver

# Сайт, на который нужно перейти
BASE_URL = "https://vkvideo.ru/"  # Замените на ваш базовый URL

# Список запросов для поиска
SEARCH_LINKS = [
    "Кстати",
    "Побег из шоушенка",
    "Азбука морзе",
    "Море",
    "Женщина"
]

def open_browser_and_search(query):
    """Открывает браузер, переходит на сайт и выполняет поиск."""
    options = Options()
    options.add_argument("--start-maximized")
    
    service = Service(CHROME_DRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Переходим на базовый сайт
        driver.get(BASE_URL)
        
        # Ждём загрузку поля поиска
        wait = WebDriverWait(driver, 3)
        search_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'input[data-testid="top-search-video-input"]')))
        
        # Очищаем поле поиска
        search_input.clear()
        
        # Вводим запрос в поле поиска
        search_input.send_keys(query)
        
        # Эмулируем нажатие клавиши Enter
        search_input.send_keys(Keys.RETURN)
        
        # Ждём несколько секунд для проверки результатов поиска
        print(f"Поиск выполнен для запроса: {query}")
        asyncio.run(asyncio.sleep(5))  # Можно убрать или изменить время ожидания
        
    except Exception as e:
        print(f"Ошибка при выполнении поиска для запроса '{query}': {e}")
    
    finally:
        # Закрываем браузер
        driver.quit()

async def main():
    # Создаем список задач для каждого запроса
    tasks = [asyncio.to_thread(open_browser_and_search, query) for query in SEARCH_LINKS]
    
    # Запускаем все задачи параллельно
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())