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


from bot.admin_chat import admin_router
from bot.dialogs import picture_router, start_router

fallback_router = Router()

BOT_TOKEN = os.getenv("BOT_TOKEN") or ""
if BOT_TOKEN == "":
    raise ValueError("BOT_TOKEN environment variable is not set")


# Пустое сообщение
@fallback_router.message(StateFilter(None))
async def default_handler(message: Message) -> None:
    # todo: смешные сообщения
    await message.answer(str(message.chat.id))
    await message.answer(message.text or "Nice try!")


async def bot_main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    # dp.message.middleware(SetUserMiddleware())
    # dp.message.middleware(CheckAccessMiddleware())

    dp.include_router(start_router)
    dp.include_router(picture_router)
    dp.include_router(admin_router)
    dp.include_router(fallback_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(bot_main())

# python -m bot.main