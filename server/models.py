from enum import Enum
from tortoise import Model, Tortoise
from tortoise import fields
from tortoise.fields import OnDelete


async def init_orm():
    await Tortoise.init(
        db_url="postgres://postgres:1@localhost:5432/imbnow",
        modules={"models": ["server.models"]},
        _enable_global_fallback=True,
    )
    await Tortoise.generate_schemas() 

async def close_orm():
    await Tortoise.close_connections()


class User(Model):

    class AccountState(str, Enum):
        ACTIVE = "ACTIVE"
        LOCKED = "LOCKED"
        BANNED = "BANNED"

    class Faculty(str, Enum):
        KTU = "КТУ"
        TINT = "ТИНТ"
        NOZ = "НОЖ"
        FTMI = "ФТМИ"
        FTMF = "ФТМФ"

    # Информация об аккаунте
    id = fields.BigIntField(primary_key=True)
    tg_id = fields.BigIntField(unique=True, db_index=True)
    tg_tag = fields.CharField(max_length=256)
    account_state = fields.CharEnumField(AccountState, default=AccountState.ACTIVE)

    # Данные пользователя, он может их свободно менять
    username = fields.CharField(max_length=256)
    faculty = fields.CharEnumField(Faculty, null=True)
    _req_member = fields.BooleanField(null=True)
    _req_organizer = fields.BooleanField(null=True)
    _req_moderator = fields.BooleanField(null=True)

    # Данные пользователя, ИСТИННЫЕ!
    is_member = fields.BooleanField(default=False)
    is_organizer = fields.BooleanField(default=False)
    is_moderator = fields.BooleanField(default=False)
    
    def get_user_image_daily_limit(self) -> int:
        if self.is_organizer:
            return 50
        if self.is_member:
            return 10
        return 1

    class Meta(Model.Meta):
        table="users"
    


class Picture(Model):

    class State(str, Enum):
        UNCHECKED = "UNCHECKED"
        MANUAL_CHECK = "MANUAL_CHECK"
        ACCEPTED = "ACCEPTED"
        REJECTED = "REJECTED"

    id = fields.IntField(primary_key=True)
    filename = fields.CharField(max_length=256)
    tg_id = fields.CharField(max_length=256)
    created_by = fields.ForeignKeyField(User, on_delete=OnDelete.CASCADE)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    state = fields.CharEnumField(State, default=State.UNCHECKED)
    check_details = fields.CharField(max_length=256, default="")
    label = fields.CharField(max_length=256)
    accepted_at = fields.DatetimeField(null=True)

