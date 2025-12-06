import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message

from src.config import settings
from src.db.session import engine
from src.db.models import Base
from src.keyboards import main_hint_keyboard
from src.handlers.media_flow import router as media_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def on_startup():
    """Создаём таблицы в БД при старте."""
    logger.info("Создаём таблицы...")
    Base.metadata.create_all(bind=engine)
    logger.info("Таблицы готовы.")


async def main() -> None:
    logger.info("Старт main()")

    if not settings.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Проверь .env")

    await on_startup()

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    dp.include_router(media_router)

    @dp.message(F.text == "/start")
    async def cmd_start(message: Message):
        await message.answer(
            "👋 Здравствуйте!\n\n"
            "Это бот «Мозг Таможни».\n\n"
            "Отправьте файл, фото или голосовое сообщение — я сохраню это в базу знаний.",
            reply_markup=main_hint_keyboard(),
        )

    logger.info("Запускаем polling...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception("Бот упал с ошибкой")
        raise e


if __name__ == "__main__":
    asyncio.run(main())
