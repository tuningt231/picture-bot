from aiogram import Bot, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter
import logging as log


from bot.api import Api


router = Router()


class StartDialog(StatesGroup):
    IS_SUBSCRIBER = State()


@router.message(Command("start"), StateFilter(None))
async def command_start_handler(message: Message, state: FSMContext, bot: Bot) -> None:
    assert message.from_user is not None
    await state.clear()
    # todo: картинка и более лучший текст
    await message.answer("Привет! 👋 Добро пожаловать в бот MEGABATTLE NOW. \n\nПоделись фото своей подготовки к гала-концерту — это может быть костюм, репетиция или просто атмосфера подготовки. Твоё фото появится на экранах в холле 2 этажа")

    user = await Api.getUser(message.from_user.id)
    if user is not None:
        await message.answer("Ты уже зарегистрирован.")
        return
    
    await check_subscription(message, state, bot)


async def check_subscription(message: Message, state: FSMContext, bot: Bot) -> None:
    # assert message.from_user is not None
    # await message.answer("Проверяю подписку на @itmomegabattle")
    # try:
    #     member = await bot.get_chat_member("@itmomegabattle", message.from_user.id)
    #     is_subscribed = member.status in ("member", "administrator", "creator")
    # except Exception:
    #     log.warning(
    #         f'Not able to check user {message.from_user.id} subscription')
    #     is_subscribed = False

    # todo:
    is_subscribed = True
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


@router.message(StateFilter(StartDialog.IS_SUBSCRIBER))
async def handle_is_subscriber(message: Message, state: FSMContext, bot: Bot) -> None:
    await check_subscription(message, state, bot)


async def finish_registration(message: Message, state: FSMContext, bot: Bot) -> None:
    assert message.from_user is not None
    user = message.from_user
    await state.clear()

    try:
        await Api.createUser(
            tg_id=user.id,
            tg_tag=user.username or "",
            username=user.full_name,
        )
        await message.answer("Готов принимать фото!", reply_markup=ReplyKeyboardRemove())
    except:
        await message.answer("Ошибка регистрации", reply_markup=ReplyKeyboardRemove())

