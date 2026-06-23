from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import get_config
from database.service.lottery import LotteryService

router = Router()


class CreateLotteryState(StatesGroup):
    waiting_for_prize = State()
    waiting_for_price = State()
    waiting_for_total = State()
    waiting_for_channel = State()


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


@router.message(CreateLotteryState.waiting_for_total, F.text.isdigit())
async def process_total(message: Message, state: FSMContext):
    await state.update_data(total=int(message.text))
    await message.answer(
        "Перешлите любое сообщение из канала, куда нужно отправить итоговый пост (или введите ID канала, например -100123456789):")
    await state.set_state(CreateLotteryState.waiting_for_channel)


@router.message(CreateLotteryState.waiting_for_channel)
async def process_channel(message: Message, state: FSMContext):
    try:
        channel_id = (
            message.forward_from_chat.id
            if message.forward_from_chat
            else int(message.text)
        )
    except ValueError:
        await message.answer("❌ Укажите корректный ID канала.")
        return

    try:
        # Проверяем, есть ли бот в чате
        me = await message.bot.get_me()
        member = await message.bot.get_chat_member(channel_id, me.id)

        if member.status in ("left", "kicked"):
            await message.answer(
                "❌ Бот не состоит в указанном канале/группе. Добавьте бота и выдайте ему необходимые права."
            )
            return

    except TelegramBadRequest:
        await message.answer(
            "❌ Не удалось получить информацию о канале.\n"
            "Убедитесь, что бот добавлен в канал/группу и имеет доступ к нему."
        )
        return

    data = await state.get_data()

    await LotteryService.create(
        data["prize"],
        data["price"],
        data["total"],
        channel_id
    )

    await message.answer(
        f"✅ Лотерея создана!\n"
        f"Приз: {data['prize']}\n"
        f"Цена: {data['price']}\n"
        f"Всего билетов: {data['total']}"
    )

    await state.clear()