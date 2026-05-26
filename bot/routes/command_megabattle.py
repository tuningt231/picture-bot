import os
import re
from aiogram import F, Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command, StateFilter
import logging as log

from bot.api import Api

ADMIN_CHAT = int(os.getenv("ADMIN_CHAT") or 0)
if ADMIN_CHAT == 0:
    raise ValueError("ADMIN_CHAT environment variable is not set")


class MegabattleDialog(StatesGroup):
    ACTIVE = State()


router = Router()


# @router.message(Command("megabattle"), StateFilter(None))
# async def command_start_handler(message: Message, state: FSMContext) -> None:
#     assert message.from_user is not None
#     user = await Api.getUser(message.from_user.id)

#     if user is not None and user["is_member"]:
#         await message.answer("Ты уже подтвердил свое участие.")
#     else:
#         await state.set_state(MegabattleDialog.ACTIVE)
#         await message.answer("Следующее сообщение будет отправлено в проверку")


# @router.message(Command("cancel"), StateFilter(MegabattleDialog))
# async def command_cancel_handler(message: Message, state: FSMContext) -> None:
#     await state.clear()
#     await message.answer("Действие отменено")


# @router.message(StateFilter(MegabattleDialog.ACTIVE))
# async def support_message_handler(message: Message, state: FSMContext, bot: Bot) -> None:
#     assert message.from_user is not None
#     await state.clear()

#     await message.copy_to(ADMIN_CHAT)
#     await bot.send_message(ADMIN_CHAT, f"Участвует ли @{message.from_user.username} "
#                            f"({message.from_user.full_name}) в мегабаттл\n"
#                            "Статус: ?",
#                            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
#                                InlineKeyboardButton(
#                                    text="Да✅", callback_data=f"megabattle_approve:{message.from_user.id}"),
#                                InlineKeyboardButton(
#                                    text="Нет❌", callback_data=f"megabattle_reject:{message.from_user.id}"),
#                            ]]))
#     await message.answer("Сообщение отправлено в поддержку")

# def _replace_status(text: str, new_status: str) -> str:
#     return re.sub(r"^Статус:.*$", f"Статус: {new_status}", text, flags=re.MULTILINE)


# @router.callback_query(F.data.startswith("megabattle_approve:"))
# async def handle_megabattle_approve(callback: CallbackQuery, bot: Bot) -> None:
#     assert callback.data is not None
#     user_id = int(callback.data.split(":")[1])

#     await Api.approveMember(user_id)
#     await bot.send_message(user_id, "Твоё участие в мегабаттле подтверждено!")

#     if isinstance(callback.message, Message):
#         new_text = _replace_status(callback.message.text or "", "Подтверждено✅")
#         await callback.message.edit_text(new_text, reply_markup=None)

#     await callback.answer("Подтверждено✅")


# @router.callback_query(F.data.startswith("megabattle_reject:"))
# async def handle_megabattle_reject(callback: CallbackQuery, bot: Bot) -> None:
#     assert callback.data is not None
#     user_id = int(callback.data.split(":")[1])

#     await Api.rejectMember(user_id)
#     await bot.send_message(user_id, "Твоё участие в мегабаттле отклонено.")

#     if isinstance(callback.message, Message):
#         new_text = _replace_status(callback.message.text or "", "Отклонено❌")
#         await callback.message.edit_text(new_text, reply_markup=None)

#     await callback.answer("Отклонено❌")
    
