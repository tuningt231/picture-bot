import asyncio
import os
import uuid
from pathlib import Path

import aiohttp
from aiogram import F, Router
from aiogram.types import Message

from bot.admin_chat import AdminChat
from bot.api import Api
from bot.detector import detect_safe_search


picture_router = Router()

# Media group accumulation: group_id -> messages / flush task
_group_messages: dict[str, list[Message]] = {}
_group_tasks: dict[str, asyncio.Task] = {}

SHARED_PATH = os.getenv("SHARED_PATH") or ""
if SHARED_PATH == "":
    raise ValueError("SHARED_PATH environment variable is not set")
if not Path(SHARED_PATH).is_dir():
    raise Exception("SHARED_PATH is not an existing directory")

@picture_router.message(F.photo)
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
    uploaded = 0
    hit_limit = False

    user_info = await Api.getUser(tg_id)

    for msg in messages:
        if hit_limit:
            break

        assert msg.photo is not None
        photo = msg.photo[-1]  # largest available size
        label = msg.caption or ""
        filepath = photos_dir / f"{uuid.uuid4()}.jpg"

        await first.bot.download(photo, destination=filepath)

        try:
            passed, details = await asyncio.to_thread(detect_safe_search, str(filepath))
        except Exception as e:
            passed, details = False, f"Ошибка детектора: {e}"

        try:
            photo_id = await Api.upload(tg_id, label, str(filepath), photo.file_id)
            uploaded += 1
            if user_info:
                await AdminChat.sendVerification(photo.file_id, user_info, photo_id, "UNCHECKED", passed, details, first.bot)
        except aiohttp.ClientResponseError as e:
            filepath.unlink(missing_ok=True)
            if e.status == 404:
                await first.answer("Упс. Похоже, ты не зарегистрирован. Используй /start для регистрации.")
                return
            elif e.status == 429:
                hit_limit = True
            else:
                raise

    if uploaded:
        word = "Фото" if uploaded == 1 else f"{uploaded} фото"
        await first.answer(f"{word} успешно загружено!")
    if hit_limit:
        await first.answer("Достигнут дневной лимит загрузки фотографий. Приходи завтра!")
