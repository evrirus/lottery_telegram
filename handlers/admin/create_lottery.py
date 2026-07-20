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
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "🎁 <b>Создание розыгрыша</b>\n\n"
        "Шаг 1/6 — укажите приз\n\n"
        "Введите название приза:\n"
        "Например: <i>iPhone 17 Pro 256GB</i>"
    )
    await state.set_state(CreateLotteryState.waiting_for_prize)


@router.message(CreateLotteryState.waiting_for_prize)
async def process_prize(message: Message, state: FSMContext):
    await state.update_data(prize=message.text)
    await message.answer(
        "💰 <b>Создание розыгрыша</b>\n\n"
        "Шаг 2/6 — цена билета\n\n"
        "Введите стоимость одного билета в рублях:\n"
        "Например: <code>100</code>"
    )
    await state.set_state(CreateLotteryState.waiting_for_price)


@router.message(CreateLotteryState.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    if not message.text:
        return await message.answer("❌ Введите стоимость билета числом")

    try:
        price = int(message.text.replace(" ", ""))
    except ValueError:
        return await message.answer(
            "❌ Некорректная цена\n\n"
            "Введите сумму числом:\n"
            "Например: <code>100</code> ₽"
        )

    if price < 100:
        return await message.answer(
            "❌ Минимальная стоимость билета — 100 ₽"
        )

    if price > 1_000_000:
        return await message.answer(
            "❌ Слишком большая стоимость билета"
        )

    await state.update_data(price=price)

    await message.answer(
        "🎟 <b>Шаг 3/6 — количество билетов</b>\n\n"
        "Введите общее количество билетов:\n"
        "Например: <code>1000</code>"
    )

    await state.set_state(CreateLotteryState.waiting_for_total)

@router.message(CreateLotteryState.waiting_for_total)
async def process_total(message: Message, state: FSMContext):
    if not message.text:
        return await message.answer(
            "❌ Введите количество билетов числом"
        )

    try:
        total = int(message.text.replace(" ", ""))
    except ValueError:
        return await message.answer(
            "❌ Некорректное количество\n\n"
            "Введите число:\n"
            "Например: <code>1000</code>"
        )

    # if total < 10:
    #     return await message.answer(
    #         "❌ Минимальное количество билетов — 10"
    #     )
    #
    if total > 1_000_000:
        return await message.answer(
            "❌ Слишком большое количество билетов"
        )

    await state.update_data(total=total)

    await message.answer(
        "📢 <b>Шаг 4/6 — канал публикации</b>\n\n"
        "Перешлите сообщение из канала\n"
        "или отправьте ID канала.\n\n"
        "Пример:\n"
        "<code>-1001234567890</code>"
    )

    await state.set_state(CreateLotteryState.waiting_for_channel)
@router.callback_query(
    CreateLotteryState.waiting_for_publish,
    F.data == "lottery_add_photo"
)
async def add_photo(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreateLotteryState.waiting_for_photo)

    await callback.message.edit_text(
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

    lottery = await LotteryService.create(
        data["prize"],
        data["price"],
        data["total"],
        data["channel_id"],
        data.get("photo")
    )

    await callback.message.edit_text(
        "✅ <b>Розыгрыш создан!</b>\n\n"
        f"🎁 {lottery.prize}\n"
        f"🎟 Билетов: {lottery.total_tickets}\n"
        f"💰 Цена: {lottery.ticket_price} ₽"
    )

    await state.clear()

from aiogram.exceptions import TelegramBadRequest


@router.message(CreateLotteryState.waiting_for_channel)
async def process_channel(message: Message, state: FSMContext):
    channel_id = None

    # Пересланное сообщение из канала
    if message.forward_from_chat:
        channel_id = message.forward_from_chat.id

    # ID или username канала
    elif message.text:
        channel = message.text.strip()

        if channel.startswith("@"):
            channel_id = channel
        else:
            try:
                channel_id = int(channel)
            except ValueError:
                return await message.answer(
                    "❌ Укажите корректный канал.\n\n"
                    "Примеры:\n"
                    "<code>-1001234567890</code>\n"
                    "<code>@my_channel</code>"
                )

    else:
        return await message.answer(
            "❌ Перешлите сообщение из канала или отправьте ID канала."
        )

    try:
        bot = message.bot

        me = await bot.get_me()
        member = await bot.get_chat_member(
            chat_id=channel_id,
            user_id=me.id
        )

        if member.status in ("left", "kicked"):
            return await message.answer(
                "❌ Бот не добавлен в этот канал.\n\n"
                "Добавьте бота как администратора."
            )

    except TelegramBadRequest:
        return await message.answer(
            "❌ Не удалось найти канал.\n\n"
            "Проверьте ID или убедитесь, что бот имеет доступ."
        )

    chat = await message.bot.get_chat(channel_id)

    await state.update_data(
        channel_id=channel_id,
        channel_title=chat.title
    )

    data = await state.get_data()

    await message.answer(
        "🎲 <b>Проверьте данные розыгрыша:</b>\n\n"
        f"🎁 Приз: {data['prize']}\n"
        f"💰 Билет: {data['price']} ₽\n"
        f"🎫 Билетов: {data['total']}\n"
        f"📢 Канал: {chat.title}\n\n"
        f"💵 Максимальный сбор: "
        f"{data['price'] * data['total']:,} ₽".replace(',', ' '),
        reply_markup=lottery_preview_keyboard()
    )

    await state.set_state(CreateLotteryState.waiting_for_publish)