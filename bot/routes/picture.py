import asyncio
import os
import re
import uuid
from pathlib import Path

import aiohttp
from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.api import Api
from bot.detector import detect_safe_search


router = Router()

_group_messages: dict[str, list[Message]] = {}
_group_tasks: dict[str, asyncio.Task] = {}

SHARED_PATH = os.getenv("SHARED_PATH") or ""
if SHARED_PATH == "":
    raise ValueError("SHARED_PATH environment variable is not set")
if not Path(SHARED_PATH).is_dir():
    raise Exception("SHARED_PATH is not an existing directory")

ADMIN_CHAT = int(os.getenv("ADMIN_CHAT") or 0)
if ADMIN_CHAT == 0:
    raise ValueError("ADMIN_CHAT environment variable is not set")


def _verification_keyboard(photo_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="Одобрить✅", callback_data=f"approve_picture:{photo_id}"),
        InlineKeyboardButton(
            text="Отклонить❌", callback_data=f"reject_picture:{photo_id}"),
    ]])


def _replace_status(caption: str, new_status: str) -> str:
    return re.sub(r"^Статус:.*$", f"Статус: {new_status}", caption, flags=re.MULTILINE)


@router.message(F.photo, StateFilter(None))
async def handle_photo(message: Message) -> None:
    if message.media_group_id:
        gid = message.media_group_id
        _group_messages.setdefault(gid, []).append(message)
        if gid in _group_tasks:
            _group_tasks[gid].cancel()
        _group_tasks[gid] = asyncio.create_task(_flush_group(gid))
    else:
        await _process_messages([message])


async def _flush_group(gid: str) -> None:
    await asyncio.sleep(0.5)
    messages = _group_messages.pop(gid, [])
    _group_tasks.pop(gid, None)
    if messages:
        await _process_messages(messages)


async def _process_messages(messages: list[Message]) -> None:
    first = messages[0]
    assert first.from_user is not None
    assert first.bot is not None

    photos_dir = Path(SHARED_PATH)
    tg_id = first.from_user.id
    bot = first.bot

    # Step 1: download and upload all photos
    uploaded: list[tuple[str, int, str]] = []  # (file_id, photo_id, filepath)
    hit_limit = False

    for msg in messages:
        if hit_limit:
            break
        if msg.photo is None:
            continue
        
        photo = msg.photo[-1]
        label = msg.caption or ""
        filepath = str(photos_dir / f"{uuid.uuid4()}.jpg")

        await bot.download(photo, destination=filepath)

        try:
            photo_id = await Api.upload(tg_id, label, filepath, photo.file_id)
            uploaded.append((photo.file_id, photo_id, filepath))
        except aiohttp.ClientResponseError as e:
            Path(filepath).unlink(missing_ok=True)
            if e.status == 404:
                await first.answer("Упс. Похоже, ты не зарегистрирован. Используй /start для регистрации.")
                return
            elif e.status == 429:
                hit_limit = True
            else:
                raise

    # Step 2: notify user
    if uploaded:
        await first.answer(f"Фотографии загружены, после проверки они появятся на экранах")
    if hit_limit:
        await first.answer("Упс. Ты достиг дневного лимита загрузки фотографий. Приходи завтра!")

    # Step 3: auto-check + send to admin chat
    for file_id, photo_id, filepath in uploaded:
        try:
            passed, details = await asyncio.to_thread(detect_safe_search, filepath)
        except Exception as e:
            passed, details = False, f"Ошибка детектора: {e}"

        if passed:
            await Api.approve(photo_id)
        else:
            await Api.reject(photo_id)

        await bot.send_photo(
            ADMIN_CHAT,
            photo=file_id,
            caption=(
                f"Статус: {'Одобрено✅' if passed else 'Отклонено❌'} (auto)\n\n"
                f"Пользователь: @{first.from_user.username} ({first.from_user.full_name})\n"
                f"Фото #{photo_id}\n\n"
                f"{details}\n"
            ),
            reply_markup=_verification_keyboard(photo_id),
        )


@router.callback_query(F.data.startswith("approve_picture:"))
async def handle_approve(callback: CallbackQuery) -> None:
    assert callback.data is not None
    assert callback.from_user is not None

    photo_id = int(callback.data.split(":")[1])
    await Api.approve(photo_id)

    if isinstance(callback.message, Message):
        await callback.message.edit_caption(caption=_replace_status(
            callback.message.caption or "",
            f"Одобрено✅ (by @{callback.from_user.username or callback.from_user.full_name})"),
            reply_markup=_verification_keyboard(photo_id)
        )
    await callback.answer("Фото одобрено✅")


@router.callback_query(F.data.startswith("reject_picture:"))
async def handle_reject(callback: CallbackQuery) -> None:
    assert callback.data is not None
    assert callback.from_user is not None

    photo_id = int(callback.data.split(":")[1])
    await Api.reject(photo_id)

    if isinstance(callback.message, Message):
        await callback.message.edit_caption(caption=_replace_status(
            callback.message.caption or "",
            f"Отклонено❌ (by @{callback.from_user.username or callback.from_user.full_name})"),
            reply_markup=_verification_keyboard(photo_id)
        )
    await callback.answer("Фото отклонено❌")
