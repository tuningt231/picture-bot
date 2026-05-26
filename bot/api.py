import aiohttp
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"


class Api:
    @staticmethod
    async def createUser(tg_id: int, tg_tag: str, username: str) -> int:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/users", json={
                "tg_id": tg_id,
                "tg_tag": tg_tag,
                "username": username,
            }) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["id"]

    @staticmethod
    async def upload(tg_id: int, label: str, filepath: str, photo_tg_id: str) -> int:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/users/{tg_id}/pictures", json={
                "filename": filepath,
                "tg_id": photo_tg_id,
                "label": label,
            }) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["id"]

    @staticmethod
    async def getUser(tg_id: int) -> dict | None:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/users/{tg_id}") as resp:
                if resp.status == 404:
                    return None
                resp.raise_for_status()
                return await resp.json()

    @staticmethod
    async def getPicture(photo_id: int) -> dict | None:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/pictures/{photo_id}") as resp:
                if resp.status == 404:
                    return None
                resp.raise_for_status()
                return await resp.json()

    @staticmethod
    async def approve(photo_id: int) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.patch(f"{BASE_URL}/pictures/{photo_id}", json={
                "accepted": True,
                "accepted_at": datetime.now(timezone.utc).isoformat(),
            }) as resp:
                resp.raise_for_status()

    @staticmethod
    async def reject(photo_id: int) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.patch(f"{BASE_URL}/pictures/{photo_id}", json={
                "accepted": False,
                "accepted_at": None
            }) as resp:
                resp.raise_for_status()

    @staticmethod
    async def approveMember(tg_id: int) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.patch(f"{BASE_URL}/users/{tg_id}", json={
                "is_member": True,
            }) as resp:
                resp.raise_for_status()

    @staticmethod
    async def rejectMember(tg_id: int) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.patch(f"{BASE_URL}/users/{tg_id}", json={
                "is_member": False,
            }) as resp:
                resp.raise_for_status()
