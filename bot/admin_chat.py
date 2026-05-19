import os

from aiogram import Bot, F, Router
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot.api import Api


ADMIT_CHAT = int(os.getenv("ADMIT_CHAT") or 0)
if ADMIT_CHAT == 0:
    raise ValueError("ADMIT_CHAT environment variable is not set")

admin_router = Router()

_STATE_LABELS = {
    "UNCHECKED": "Не проверено",
    "MANUAL_CHECK": "Требует ручной проверки",
    "ACCEPTED": "Принято",
    "REJECTED": "Отклонено",
}


def _verification_keyboard(photo_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Одобрить", callback_data=f"approve:{photo_id}"),
        InlineKeyboardButton(text="Отклонить", callback_data=f"reject:{photo_id}"),
    ]])


def _verification_caption(user_info: dict, photo_id: int, state: str, passed: bool, details: str) -> str:
    tag = f"@{user_info['tg_tag']}" if user_info.get("tg_tag") else "—"
    faculty = user_info.get("faculty") or "—"
    state_label = _STATE_LABELS.get(state, state)
    auto_check = "Прошла" if passed else "Не прошла"
    return (
        f"Новое фото на верификацию\n\n"
        f"Пользователь: {user_info.get('username', '—')}\n"
        f"Тег: {tag}\n"
        f"Факультет: {faculty}\n"
        f"Фото #{photo_id}\n\n"
        f"Автопроверка: {auto_check}\n"
        f"{details}\n\n"
        f"Статус: {state_label}"
    )


class AdminChat:
    @staticmethod
    async def infoMessage(text: str, bot: Bot) -> None:
        await bot.send_message(ADMIT_CHAT, text)

    @staticmethod
    async def sendVerification(photo_file_id: str, user_info: dict, photo_id: int, state: str, passed: bool, details: str, bot: Bot) -> None:
        caption = _verification_caption(user_info, photo_id, state, passed, details)
        await bot.send_photo(
            ADMIT_CHAT,
            photo=photo_file_id,
            caption=caption,
            reply_markup=_verification_keyboard(photo_id),
        )


def _replace_status(caption: str, new_state: str) -> str:
    state_label = _STATE_LABELS.get(new_state, new_state)
    return "\n".join(
        f"Статус: {state_label}" if line.startswith("Статус:") else line
        for line in caption.split("\n")
    )


@admin_router.callback_query(F.data.startswith("approve:"))
async def handle_approve(callback: CallbackQuery) -> None:
    assert callback.data is not None
    photo_id = int(callback.data.split(":")[1])
    await Api.approve(photo_id)
    if isinstance(callback.message, Message):
        new_caption = _replace_status(callback.message.caption or "", "ACCEPTED")
        await callback.message.edit_caption(caption=new_caption, reply_markup=None)
    await callback.answer("Фото одобрено")


@admin_router.callback_query(F.data.startswith("reject:"))
async def handle_reject(callback: CallbackQuery) -> None:
    assert callback.data is not None
    photo_id = int(callback.data.split(":")[1])
    await Api.reject(photo_id)
    if isinstance(callback.message, Message):
        new_caption = _replace_status(callback.message.caption or "", "REJECTED")
        await callback.message.edit_caption(caption=new_caption, reply_markup=None)
    await callback.answer("Фото отклонено")
