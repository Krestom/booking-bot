# run.py
import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from app.handlers import router
from app.scheduler import scheduler
from app.database import init_db

logging.getLogger('selenium').setLevel(logging.CRITICAL)
logging.getLogger('webdriver').setLevel(logging.CRITICAL)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", mode="a", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

async def main():
    load_dotenv()
    init_db()
    bot = Bot(token=os.getenv('TG_TOKEN'))
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Начать бронирование"),
        BotCommand(command="my_bookings", description="Мои активные заявки")
    ])

    asyncio.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info('Бот остановлен пользователем')