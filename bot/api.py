import aiohttp

BASE_URL = "http://localhost:8000"


class Api:
    @staticmethod
    async def createUser(tg_id: int, tg_tag: str, username: str, faculty: str | None = None) -> int:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/users", json={
                "tg_id": tg_id,
                "tg_tag": tg_tag,
                "username": username,
                "faculty": faculty,
            }) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["id"]

    @staticmethod
    async def upload(tg_id: int, label: str, filepath: str, photo_tg_id: str) -> int:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/upload", json={
                "tg_id": tg_id,
                "label": label,
                "filepath": filepath,
                "photo_tg_id": photo_tg_id,
            }) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data["id"]

    # @staticmethod
    # async def updateUser(
    #     tg_id: int,
    #     username: str | None = None,
    #     faculty: str | None = None,
    #     req_member: bool | None = None,
    #     req_organizer: bool | None = None,
    #     req_moderator: bool | None = None,
    # ) -> None:
    #     async with aiohttp.ClientSession() as session:
    #         async with session.patch(f"{BASE_URL}/users", json={
    #             "tg_id": tg_id,
    #             "username": username,
    #             "faculty": faculty,
    #             "req_member": req_member,
    #             "req_organizer": req_organizer,
    #             "req_moderator": req_moderator,
    #         }) as resp:
    #             resp.raise_for_status()

    @staticmethod
    async def getUser(tg_id: int) -> dict | None:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/users", params={"tg_id": tg_id}) as resp:
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
            async with session.post(f"{BASE_URL}/pictures/{photo_id}/approve") as resp:
                resp.raise_for_status()

    @staticmethod
    async def reject(photo_id: int) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/pictures/{photo_id}/reject") as resp:
                resp.raise_for_status()
