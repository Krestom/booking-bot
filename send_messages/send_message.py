import os
import asyncio
from aiogram import Bot
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv(dotenv_path="./.env")

# Инициализация бота
bot = Bot(token=os.getenv('TG_TOKEN'))

async def send_message(user_id: int, message: str):
    """
    Отправляет текстовое сообщение пользователю по его user_id.
    """
    try:
        # Отправка текстового сообщения
        await bot.send_message(chat_id=user_id, text=message, disable_notification=True)
        print(f"Сообщение успешно отправлено пользователю {user_id}")
    except Exception as e:
        print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")

async def main():
    # Список Telegram ID получателей
    user_ids = [
        821280990,  # Илья
        960680945,  # Полина
        855505730,  # Никита
        649692530,  # Ваге
        1465533850,  # Арина
        1031964007,  # Ксюша
        759223609, # Рома
    ]

    # Текст сообщения
    message_text = '''Бот работает, можно записываться'''

    # Отправка текстовых сообщений
    for user_id in user_ids:
        await send_message(user_id, message_text)

    # Закрытие сессии бота
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
