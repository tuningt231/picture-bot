import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import StateFilter, Command, MagicData
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove


import bot.routes as routes
from bot.middleware import BanCheckMiddleware

fallback_router = Router()

BOT_TOKEN = os.getenv("BOT_TOKEN") or ""
if BOT_TOKEN == "":
    raise ValueError("BOT_TOKEN environment variable is not set")


# Пустое сообщение
@fallback_router.message(StateFilter(None))
async def default_handler(message: Message) -> None:
    # todo: смешные сообщения
    # await message.answer(str(message.photo[-1].file_id))
    # await message.answer(str(message.photo[-1].file_unique_id))
    await message.answer("Отправь фотографию или команду🙂")
    


async def bot_main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    dp.update.middleware(BanCheckMiddleware())

    dp.include_router(routes.start_router)
    dp.include_router(routes.megabattle_router)
    dp.include_router(routes.support_router)
    dp.include_router(routes.picture_router)
    dp.include_router(fallback_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(bot_main())

# python -m bot.main