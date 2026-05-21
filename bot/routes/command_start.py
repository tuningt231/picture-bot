from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import Command
import logging as log


from bot.api import Api


router = Router()


class StartDialog(StatesGroup):
    IS_SUBSCRIBER = State()


@router.message(Command("start"))
async def command_start_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    assert message.from_user is not None
    await state.clear()
    await message.answer("Приветственное сообщение с информацией")
    user = await Api.getUser(message.from_user.id)
    if user is not None:
        await message.answer("Ты уже зарегистрирован.")
        return
    await check_subscription(message, state, bot)


async def check_subscription(message: Message, state: FSMContext, bot: Bot) -> None:
    assert message.from_user is not None
    await message.answer("Проверяю подписку на канал...")
    try:
        member = await bot.get_chat_member("@itmomegabattle", message.from_user.id)
        is_subscribed = member.status not in ("left", "kicked")
    except Exception:
        log.warning(
            f'Not able to check user {message.from_user.id} subscription')
        is_subscribed = False

    if not is_subscribed:
        await ask_subscribe(message, state)
    else:
        await finish_registration(message, state, bot)


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


@router.message(StartDialog.IS_SUBSCRIBER)
async def handle_is_subscriber(message: Message, state: FSMContext, bot: Bot) -> None:
    await check_subscription(message, state, bot)


async def finish_registration(message: Message, state: FSMContext, bot: Bot) -> None:
    assert message.from_user is not None
    user = message.from_user
    await state.clear()

    await Api.createUser(
        tg_id=user.id,
        tg_tag=user.username or "",
        username=user.full_name,
    )

    await message.answer("Регистрация завершена! Добро пожаловать!", reply_markup=ReplyKeyboardRemove())
