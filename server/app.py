from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
from tortoise.exceptions import ValidationError

from server.models import Picture, User

app = FastAPI()

register_tortoise(app,
                  db_url="postgres://postgres:1@localhost:5432/imbnow",
                  modules={"models": ["server.models"]},
                  add_exception_handlers=True,
                  generate_schemas=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
)


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"detail": str(exc)})


@app.middleware("http")
async def localhost_only_post(request: Request, call_next):
    if request.method != "GET" and (request.client is None or request.client.host not in ("127.0.0.1", "::1")):
        raise HTTPException(
            status_code=403, detail="This method is only allowed from localhost")
    return await call_next(request)


# важно сделать это до создания pydantic схем
Tortoise.init_models(["server.models"], "models")

CreateUserRequest = pydantic_model_creator(
    User, name="CreateUserRequest",
    include=('tg_id', 'tg_tag', 'username'))

UserResponse = pydantic_model_creator(
    User, name="UserResponse",
    include=('id', 'tg_id', 'tg_tag', 'username', 'is_banned',
             'is_member', 'is_organizer', 'is_moderator'))

UpdateUserRequest = pydantic_model_creator(
    User, name="UpdateUserRequest",
    include=('username', 'tg_tag', 'is_banned', 'is_member', 'is_organizer', 'is_moderator'),
    optional=('username', 'tg_tag', 'is_banned', 'is_member', 'is_organizer', 'is_moderator'))

UploadPictureRequest = pydantic_model_creator(
    Picture, name="UploadPictureRequest",
    include=('filename', 'tg_id', 'label'))

PictureResponse = pydantic_model_creator(
    Picture, name="PictureResponse",
    include=('id', 'filename', 'tg_id', 'created_at', 'accepted', 
             'check_details', 'label', 'accepted_at'))

UpdatePictureRequest = pydantic_model_creator(
    Picture, name="UpdatePictureRequest",
    include=('accepted', 'check_details', 'accepted_at'),
    optional=('accepted', 'check_details', 'accepted_at'))


# --- Пользователи ---


@app.post("/users", response_model=UserResponse)
async def create_user(body: CreateUserRequest):  # type: ignore
    user = await User.create(**body.dict())
    return user


@app.get("/users", response_model=list[UserResponse])
async def get_all_users():
    return await User.all()


@app.get("/users/{tg_id}", response_model=UserResponse)
async def get_user(tg_id: int):
    return await User.get(tg_id=tg_id)


@app.patch("/users/{tg_id}", response_model=UserResponse)
async def patch_user(tg_id: int, body: UpdateUserRequest):  # type: ignore
    user = await User.get(tg_id=tg_id)
    await user.update_from_dict(body.dict(exclude_unset=True)).save()
    return user


# --- Изображения ---

@app.post("/users/{tg_id}/pictures", response_model=PictureResponse)
async def upload(tg_id: int, body: UploadPictureRequest):  # type: ignore
    user = await User.get(tg_id=tg_id)

    today_start = datetime.now(tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)
    daily_count = await Picture.filter(created_by=user, created_at__gt=today_start).count()
    if daily_count >= user.get_user_image_daily_limit():
        raise HTTPException(
            status_code=429, detail="Daily upload limit reached")

    if not Path(body.filename).exists():
        raise HTTPException(
            status_code=400, detail=f"File {body.filename} doesn't exist")

    picture = await Picture.create(
        filename=body.filename, tg_id=body.tg_id, created_by=user, label=body.label)
    return picture


@app.get("/pictures", response_model=list[PictureResponse])
async def get_pictures(from_date: datetime, to_date: datetime):
    return await Picture.filter(
        accepted_at__gte=from_date,
        accepted_at__lte=to_date,
        accepted=True
    ).order_by("-accepted_at")


@app.get("/pictures/{picture_id}/download")
async def download_picture(picture_id: int):
    picture = await Picture.get_or_none(id=picture_id)
    if picture is None or not Path(picture.filename).exists():
        raise HTTPException(status_code=404, detail="Picture not found")
    return FileResponse(picture.filename)


@app.patch("/pictures/{picture_id}", response_model=PictureResponse)
async def patch_picture(picture_id: int, body: UpdatePictureRequest):  # type: ignore
    picture = await Picture.get_or_none(id=picture_id)
    if picture is None:
        raise HTTPException(status_code=404, detail="Picture not found")
    await picture.update_from_dict(body.dict(exclude_unset=True)).save()
    return picture
