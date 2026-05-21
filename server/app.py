from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from server.models import Picture, User, close_orm, init_orm


app = FastAPI(
    on_startup=[init_orm],
    on_shutdown=[close_orm],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["GET"],
)


@app.middleware("http")
async def localhost_only_post(request: Request, call_next):
    if request.method == "POST" and (request.client is None or request.client.host not in ("127.0.0.1", "::1")):
        raise HTTPException(status_code=403, detail="POST requests are only allowed from localhost")
    return await call_next(request)


async def get_active_user(tg_id: int) -> User:
    user = await User.get_or_none(tg_id=tg_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.account_state == User.AccountState.BANNED:
        raise HTTPException(status_code=403, detail="Аккаунт пользователя забанен")
    if user.account_state == User.AccountState.LOCKED:
        raise HTTPException(status_code=403, detail="Аккаунт пользователя заблокирован")
    return user

# --- 1. Создание пользователя ---

class CreateUserBody(BaseModel):
    tg_id: int
    tg_tag: str
    username: str
    faculty: str | None = None


@app.post("/users")
async def create_user(body: CreateUserBody):
    user = await User.create(
        tg_id=body.tg_id,
        tg_tag=body.tg_tag,
        username=body.username,
        faculty=body.faculty,
    )
    return {"id": user.id}


# --- 2. Обновление пользователя ---

class UpdateUserBody(BaseModel):
    tg_id: int
    username: str | None = None
    faculty: str | None = None
    req_member: bool | None = None
    req_organizer: bool | None = None
    req_moderator: bool | None = None


@app.patch("/users")
async def update_user(body: UpdateUserBody):
    user = await get_active_user(body.tg_id)
    if body.username is not None:
        user.username = body.username
    if body.faculty is not None:
        user.faculty = User.Faculty(body.faculty)
    if body.req_member is not None:
        user._req_member = body.req_member
    if body.req_organizer is not None:
        user._req_organizer = body.req_organizer
    if body.req_moderator is not None:
        user._req_moderator = body.req_moderator
    await user.save()
    return {"ok": True}


# --- 3. Получение пользователя ---

@app.get("/users")
async def get_user(tg_id: int):
    user = await User.get_or_none(tg_id=tg_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "tg_id": user.tg_id,
        "tg_tag": user.tg_tag,
        "username": user.username,
        "faculty": user.faculty,
        "account_state": user.account_state,
        "is_member": user.is_member,
        "is_organizer": user.is_organizer,
        "is_moderator": user.is_moderator,
        # "req_member": user._req_member,
        # "req_moderator": user._req_moderator,
        # "req_organizer": user._req_organizer,
    }


# --- 3. Загрузка изображения ---

class UploadBody(BaseModel):
    tg_id: int
    label: str
    filepath: str
    photo_tg_id: str


@app.post("/upload")
async def upload(body: UploadBody):
    user = await get_active_user(body.tg_id)

    today_start = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    daily_count = await Picture.filter(created_by=user, created_at__gt=today_start).count()
    if daily_count >= user.get_user_image_daily_limit():
        raise HTTPException(status_code=429, detail="Daily upload limit reached")
    
    if not Path(body.filepath).exists():
        raise HTTPException(status_code=400, detail=f"File {body.filepath} doesn't exist")

    picture = await Picture.create(filename=body.filepath, tg_id=body.photo_tg_id, created_by=user, label=body.label)

    return {"id": picture.id}


# --- 4. Лента изображений для сайта ---

@app.get("/pictures")
async def get_pictures(from_date: datetime, to_date: datetime):
    res = await Picture.filter(accepted_at__gte=from_date, accepted_at__lte=to_date, state=Picture.State.ACCEPTED).select_related("created_by").order_by("-accepted_at")
    ret = []
    for picture in res:
        try:
            pic_type = "ОРГАНИЗАТОРЫ" if picture.created_by.is_organizer else picture.created_by.faculty.value
            ret.append({
                "id": picture.id,
                "label": picture.label,
                "type": pic_type,
                "accepted_at": picture.accepted_at,
            })
        except Exception:
            print(f"Error while filtering pictures: Picture({picture.id})")
    return ret


@app.get("/pictures/{picture_id}/download")
async def download_picture(picture_id: int):
    picture = await Picture.get_or_none(id=picture_id)
    if picture is None or not Path(picture.filename).exists():
        raise HTTPException(status_code=404, detail="Picture not found")
    return FileResponse(picture.filename)


# @app.get("/pictures/{picture_id}")
# async def get_picture(picture_id: int):
#     picture = await Picture.get_or_none(id=picture_id)
#     if picture is None:
#         raise HTTPException(status_code=404, detail="Picture not found")
#     return {
#         "id": picture.id,
#         "state": picture.state,
#         "label": picture.label,
#         "check_details": picture.check_details,
#     }


@app.post("/pictures/{picture_id}/approve")
async def approve_picture(picture_id: int):
    picture = await Picture.get_or_none(id=picture_id)
    if picture is None:
        raise HTTPException(status_code=404, detail="Picture not found")
    picture.state = Picture.State.ACCEPTED
    picture.accepted_at = datetime.now(timezone.utc)
    await picture.save()
    return {"ok": True}


@app.post("/pictures/{picture_id}/reject")
async def reject_picture(picture_id: int):
    picture = await Picture.get_or_none(id=picture_id)
    if picture is None:
        raise HTTPException(status_code=404, detail="Picture not found")
    picture.state = Picture.State.REJECTED
    await picture.save()
    return {"ok": True}
