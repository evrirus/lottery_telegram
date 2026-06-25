from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from config import get_config
from database.service.lottery import LotteryService
from keyboards.inline import lottery_preview_keyboard

router = Router()


class CreateLotteryState(StatesGroup):
    waiting_for_prize = State()
    waiting_for_price = State()
    waiting_for_total = State()
    waiting_for_channel = State()
    waiting_for_photo = State()
    waiting_for_publish = State()

@router.message(Command("create"))
async def cmd_create(message: Message, state: FSMContext):
    config = get_config()
    ADMIN_ID = config.ADMIN_ID
    #todo: расскоментить
    # if message.from_user.id != ADMIN_ID:
    #     return

    await message.answer("Введите описание приза:")
    await state.set_state(CreateLotteryState.waiting_for_prize)


@router.message(CreateLotteryState.waiting_for_prize)
async def process_prize(message: Message, state: FSMContext):
    await state.update_data(prize=message.text)
    await message.answer("Введите цену одного билета в $RUB:")
    await state.set_state(CreateLotteryState.waiting_for_price)


@router.message(CreateLotteryState.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число")

    price = int(message.text)

    if price < 100:
        return await message.answer("Цена билета не может быть меньше 100 ₽")

    await state.update_data(price=price)
    await message.answer("Введите общее количество билетов:")
    await state.set_state(CreateLotteryState.waiting_for_total)


@router.message(CreateLotteryState.waiting_for_total)
async def process_total(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Введите число")

    await state.update_data(total=int(message.text))

    await message.answer(
        "Перешлите сообщение из канала или введите ID канала:"
    )

    await state.set_state(CreateLotteryState.waiting_for_channel)

@router.callback_query(
    CreateLotteryState.waiting_for_publish,
    F.data == "lottery_add_photo"
)
async def add_photo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateLotteryState.waiting_for_photo)

    await callback.message.answer(
        "Отправьте фотографию для розыгрыша."
    )

    await callback.answer()


@router.message(CreateLotteryState.waiting_for_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)

    data = await state.get_data()

    await message.answer(
        "🎲 Обновлённый розыгрыш:\n\n"
        f"🎁 Приз: {data['prize']}\n"
        f"💰 Цена: {data['price']} ₽\n"
        f"🎫 Билеты: {data['total']}\n"
        f"📢 Канал: {data['channel_id']}\n"
        f"📷 Фото: добавлено",
        reply_markup=lottery_preview_keyboard()
    )

    await state.set_state(CreateLotteryState.waiting_for_publish)


@router.callback_query(
    CreateLotteryState.waiting_for_publish,
    F.data == "lottery_publish"
)
async def publish_lottery(
    callback: CallbackQuery,
    state: FSMContext
):
    data = await state.get_data()

    await LotteryService.create(
        data["prize"],
        data["price"],
        data["total"],
        data["channel_id"],
        data.get("photo")
    )

    await callback.message.edit_text(
        "✅ Лотерея создана!"
    )

    await state.clear()

@router.message(CreateLotteryState.waiting_for_channel)
async def process_channel(message: Message, state: FSMContext):
    try:
        channel_id = (
            message.forward_from_chat.id
            if message.forward_from_chat
            else int(message.text)
        )
    except ValueError:
        return await message.answer("❌ Укажите корректный ID канала.")

    try:
        me = await message.bot.get_me()
        member = await message.bot.get_chat_member(channel_id, me.id)

        if member.status in ("left", "kicked"):
            return await message.answer(
                "❌ Бот не состоит в канале."
            )

    except TelegramBadRequest:
        return await message.answer(
            "❌ Не удалось получить информацию о канале."
        )

    await state.update_data(channel_id=channel_id)

    data = await state.get_data()

    await message.answer(
        "🎲 Будет создан следующий розыгрыш:\n\n"
        f"🎁 Приз: {data['prize']}\n"
        f"💰 Цена билета: {data['price']} ₽\n"
        f"🎫 Количество билетов: {data['total']}\n"
        f"📢 Канал: {channel_id}",
        reply_markup=lottery_preview_keyboard()
    )

    await state.set_state(CreateLotteryState.waiting_for_publish)