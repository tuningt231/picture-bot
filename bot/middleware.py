import logging
import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from bot.api import Api

logger = logging.getLogger(__name__)


class BanCheckMiddleware(BaseMiddleware):
    banned_ids: list[int] = []
    last_refresh: float = 0.0

    async def refresh(self) -> None:
        try:
            users = await Api.getUsers()
            self.banned_ids = [u["tg_id"] for u in users if u.get("is_banned")]
            self.last_refresh = time.monotonic()
        except Exception:
            logger.exception("Не удалось обновить список забаненых пользователей")

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if time.monotonic() - self.last_refresh >= 300: # 5 минут
            await self.refresh()

        user = data.get("event_from_user")
        if user and user.id in self.banned_ids:
            if isinstance(event, Message):
                await event.answer("И чего ты добился? Ты забанен и больше не можешь использовать бота😈")
            return None
        return await handler(event, data)
