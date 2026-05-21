from email import message_from_string
import os
import re
from aiogram import F, Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter
import logging as log

from bot.api import Api

SUPPORT_CHAT = int(os.getenv("SUPPORT_CHAT") or 0)
if SUPPORT_CHAT == 0:
    raise ValueError("SUPPORT_CHAT environment variable is not set")


class SupportDialog(StatesGroup):
    ACTIVE = State()


router = Router()


@router.message(Command("support"))
async def command_support_handler(message: Message, state: FSMContext) -> None:
    assert message.from_user is not None
    await state.set_state(SupportDialog.ACTIVE)
    await message.answer("Следующее сообщение будет отправлено в поддержку")


@router.message(Command("cancel"), StateFilter(SupportDialog))
async def command_cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Действие отменено")


@router.message(StateFilter(SupportDialog.ACTIVE))
async def support_message_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    assert message.from_user is not None
    await state.clear()
    await bot.send_message(SUPPORT_CHAT, 
                           "Сообщение в службу поддержки от "
                           f"{message.from_user.username} ({message.from_user.full_name})\n"
                           f"Ответь на ЭТО сообщение, чтобы отправить ответ пользователю\n"
                           f"chat_id={message.chat.id}")
    await message.copy_to(SUPPORT_CHAT)
    await message.answer("Сообщение отправлено в поддержку")


@router.message(F.chat.id == SUPPORT_CHAT, F.reply_to_message)
async def support_response_handler(message: Message, bot: Bot) -> None:
    try: 
        assert message.reply_to_message is not None
        assert message.reply_to_message.text is not None
    
        res = re.findall(r'^chat_id=(\d+)', message.reply_to_message.text)
        if len(res) == 1:
            chat_id = int(res[0])
            await bot.send_message(chat_id, "У тебя новое сообщение от службы поддержки")
            await message.copy_to(chat_id)
            
    except Exception as e:
        await message.answer(f"Ошибка {e}")

    await message.answer(f"Не удалось отправить сообщение")


