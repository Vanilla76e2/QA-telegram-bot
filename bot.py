import asyncio
import logging
from loader import dp, bot
from database import init_db

# логирование в консоль и файл
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# инициализация базы
init_db()

# регистрация хендлеров
from handlers import user, manager  # noqa

async def main():
    logger.info("Запуск бота...")
    try:
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        logger.exception("Ошибка при polling бота:")
    finally:
        await bot.session.close()
        logger.info("Бот остановлен.")

if __name__ == "__main__":
    asyncio.run(main())
