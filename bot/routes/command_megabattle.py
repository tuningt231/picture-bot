import os
from aiogram import F, Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, StateFilter
import logging as log

from bot.admin_chat import AdminChat
from bot.api import Api

ADMIN_CHAT = int(os.getenv("ADMIN_CHAT") or 0)
if ADMIN_CHAT == 0:
    raise ValueError("ADMIN_CHAT environment variable is not set")


class MegabattleDialog(StatesGroup):
    ACTIVE = State()


router = Router()


@router.message(Command("megabattle"))
async def command_start_handler(message: Message, state: FSMContext) -> None:
    assert message.from_user is not None
    user = await Api.getUser(message.from_user.id)

    if user is not None and user["is_member"]:
        await message.answer("Ты уже подтвердил свое участие.")
    else:
        await state.set_state(MegabattleDialog.ACTIVE)
        await message.answer("Следующее сообщение будет отправлено в проверку")


@router.message(Command("cancel"), StateFilter(MegabattleDialog))
async def command_cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действие отменено")


@router.message(StateFilter(MegabattleDialog.ACTIVE))
async def support_message_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    assert message.from_user is not None
    await state.clear()

    await message.copy_to(ADMIN_CHAT)
    await bot.send_message(ADMIN_CHAT, f"Участвует ли {message.from_user.username} ({message.from_user.full_name}) в мегабаттл\nСтатус: ?",
                           reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                               InlineKeyboardButton(
                                   text="Да", callback_data=f"megabattle_approve:{message.from_user.id}"),
                               InlineKeyboardButton(
                                   text="Нет", callback_data=f"megabattle_reject:{message.from_user.id}"),
                           ]]))
    await message.answer("Сообщение отправлено в поддержку")

