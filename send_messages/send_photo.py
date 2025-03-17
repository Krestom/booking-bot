import os
import asyncio
from aiogram import Bot
from aiogram.types.input_file import FSInputFile  # Используем FSInputFile для локальных файлов
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv(dotenv_path=os.path.join(os.pardir, '.env'))

# Инициализация бота
bot = Bot(token=os.getenv('TG_TOKEN'))

async def send_message_with_photo(user_id: int, message: str, photo_path: str):
    """
    Отправляет сообщение с локальной фотографией пользователю по его user_id.
    """
    try:
        # Проверяем, существует ли файл
        if not os.path.exists(photo_path):
            print(f"Файл не найден: {photo_path}")
            return

        # Используем FSInputFile для отправки локального файла
        await bot.send_photo(
            chat_id=user_id,
            photo=FSInputFile(photo_path),  # Передаем путь к файлу напрямую
            caption=message,
            disable_notification=True
        )
        print(f"Сообщение с фото успешно отправлено пользователю {user_id}")
    except Exception as e:
        print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

async def main():
    # Список Telegram ID получателей
    user_ids = [
        821280990,  # Илья
        960680945, # Полина
        855505730, # Никита
        649692530, # Ваге
        1465533850, # Арина
        1031964007, # Ксюша
    ]

    # Текст сообщения
    message_text = '''Всем доброе утро и продуктивного дня!\nОставляйте заявки, в 9 утра начнутся голодные игры🤡🤡🤡'''

    # Путь к локальному файлу изображения
    photo_path = 'images_to_send/доброе_утро.jpeg'  # Убедитесь, что путь корректен

    # Проверяем существование файла перед отправкой
    if not os.path.exists(photo_path):
        print(f"Ошибка: Файл с изображением не найден по пути {photo_path}")
        return

    # Отправка сообщений с фотографиями
    for user_id in user_ids:
        await send_message_with_photo(user_id, message_text, photo_path)

    # Закрытие сессии бота
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())