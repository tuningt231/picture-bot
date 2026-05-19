from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import Command

from bot.admin_chat import AdminChat
from bot.api import Api


start_router = Router()


class StartDialog(StatesGroup):
    FACULTY = State()
    IS_MEMBER = State()
    IS_SUBSCRIBER = State()


FACULTIES = ("КТУ", "ТИНТ", "НОЖ", "ФТМИ", "ФТМФ")


def faculty_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="КТУ"), KeyboardButton(text="ТИНТ")],
            [KeyboardButton(text="НОЖ"), KeyboardButton(text="ФТМИ")],
            [KeyboardButton(text="ФТМФ")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def yes_no_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Да"), KeyboardButton(text="Нет")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


@start_router.message(Command("cancel"))
async def command_cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())


@start_router.message(Command("start"))
async def command_start_handler(message: Message, state: FSMContext) -> None:
    assert message.from_user is not None
    await state.clear()
    await message.answer("Приветственное сообщение с информацией")
    user = await Api.getUser(message.from_user.id)
    if user is not None:
        faculty = user.get("faculty") or "—"
        await message.answer(
            f"Ты уже зарегистрирован.\n\n"
            f"Имя: {message.from_user.full_name}\n"
            f"Тег: @{message.from_user.username or '—'}\n"
            f"Факультет: {faculty}\n\n"
            "Начинаем изменение данных."
        )
        await state.update_data(is_update=True)
    else:
        await message.answer("Нужна регистрация")
        await state.update_data(is_update=False)
    await ask_faculty(message, state)


async def ask_faculty(message: Message, state: FSMContext) -> None:
    await state.set_state(StartDialog.FACULTY)
    await message.answer(
        "С какого ты магафакультета?",
        reply_markup=faculty_keyboard(),
    )


@start_router.message(StartDialog.FACULTY)
async def handle_faculty(message: Message, state: FSMContext) -> None:
    if message.text is None or message.text.upper() not in FACULTIES:
        await message.answer("Сделай выбор из предложенных вариантов")
        await ask_faculty(message, state)
        return
    await state.update_data(faculty=message.text.upper())
    await ask_is_member(message, state)


async def ask_is_member(message: Message, state: FSMContext) -> None:
    await state.set_state(StartDialog.IS_MEMBER)
    await message.answer(
        "Участвуешь ли ты в Мегабаттле?",
        reply_markup=yes_no_keyboard(),
    )


@start_router.message(StartDialog.IS_MEMBER)
async def handle_is_member(message: Message, state: FSMContext, bot: Bot) -> None:
    if message.text is None or message.text.upper() not in ("ДА", "НЕТ"):
        await message.answer("Сделай выбор из предложенных вариантов")
        await ask_is_member(message, state)
        return
    await state.update_data(req_member=message.text.upper() == "ДА")
    await check_subscription(message, state, bot)


async def check_subscription(message: Message, state: FSMContext, bot: Bot) -> None:
    assert message.from_user is not None
    await message.answer("Проверяю подписку на канал...", reply_markup=ReplyKeyboardRemove())
    # todo: add bot to the channel
    # try:
    #     member = await bot.get_chat_member("@itmomegabattle", message.from_user.id)
    #     is_subscribed = member.status not in ("left", "kicked")
    # except Exception:
    #     is_subscribed = False

    # if not is_subscribed:
    #     await ask_subscribe(message, state)
    #     return

    await finish_dialog(message, state, bot)


async def ask_subscribe(message: Message, state: FSMContext) -> None:
    await state.set_state(StartDialog.IS_SUBSCRIBER)
    await message.answer(
        "Не вижу тебя среди подписчиков. Подпишись на канал @itmomegabattle и повтори попытку.",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="Готово")]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


@start_router.message(StartDialog.IS_SUBSCRIBER)
async def handle_is_subscriber(message: Message, state: FSMContext, bot: Bot) -> None:
    await check_subscription(message, state, bot)


async def finish_dialog(message: Message, state: FSMContext, bot: Bot) -> None:
    assert message.from_user is not None
    data = await state.get_data()
    faculty = data.get("faculty", "-")
    req_member = data.get("req_member", False)
    is_update = data.get("is_update", False)
    user = message.from_user

    await state.clear()

    if is_update:
        await Api.updateUser(tg_id=user.id, faculty=faculty)
        if req_member:
            await Api.request(user.id, "member")
        await message.answer("Данные обновлены!", reply_markup=ReplyKeyboardRemove())
    else:
        await Api.createUser(
            tg_id=user.id,
            tg_tag=user.username or "",
            username=user.full_name,
            faculty=faculty,
        )
        if req_member:
            await Api.request(user.id, "member")
        tag = f"@{user.username}" if user.username else user.full_name
        await AdminChat.infoMessage(f"Новый пользователь: {tag} ({user.full_name})\n", bot)
        await message.answer("Регистрация завершена! Добро пожаловать!", reply_markup=ReplyKeyboardRemove())
