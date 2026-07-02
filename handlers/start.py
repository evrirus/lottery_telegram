import logging
import os
from decimal import Decimal

import dotenv
from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InputMediaPhoto
from aiogram.utils.payload import decode_payload
from async_cb_rate.parser import get_rate
from lava_top_sdk import LavaClient, LavaClientConfig, LogLevel, Currency, PaymentMethod

from database.service.lottery import LotteryService
from database.service.user import UserService
from keyboards.inline import get_ticket_quantity_keyboard, get_active_lotteries_keyboard, start_keyboard, \
    last_keyboard_buy, inline_exit_to_payment_method
from service.cryptobot import create_cryptobot_invoice

dotenv.load_dotenv()

logger = logging.getLogger()
router_start = Router()
config = LavaClientConfig(
    api_key=os.getenv("LAVATOP_TOKEN"),
    env='production',  # or 'production' or 'sandbox'
    webhook_secret_key='your-webhook-secret',
    logging_level=LogLevel.DEBUG
)

client = LavaClient(config)

@router_start.message(CommandStart(
    deep_link=True,
    deep_link_encoded=True
))
async def cmd_start(message: types.Message, command: CommandObject):
    payload = command.args

    # await UserService.register(message.from_user.id, referrer_id=referrer_id)
    await message.answer(
        f"Выберите действие, payload: {payload}",
        reply_markup=start_keyboard()
    )

@router_start.message(CommandStart())
async def cmd_start(message: types.Message):
    await UserService.register(message.from_user.id)
    await message.answer(
        "Выберите действие",
        reply_markup=start_keyboard()
    )

@router_start.callback_query(F.data == "start")
async def cmd_start(cbd: CallbackQuery):
    await cbd.message.edit_text(
        "Выберите действие",
        reply_markup=start_keyboard()
    )

@router_start.callback_query(lambda c: c.data == "lotteries")
async def cmd_lotteries(cbd: types.CallbackQuery):
    await show_lotteries_list(cbd)


async def show_lotteries_list(target: types.Message | types.CallbackQuery):
    lotteries = await LotteryService.get_actives()

    text = (
        "📋 <b>Список активных лотерей:</b>\n\n"
        "Выберите интересующую вас лотерею:"
    )

    keyboard = (
        get_active_lotteries_keyboard(lotteries)
        if lotteries
        else InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❌ Отмена", callback_data="start")]
            ]
        )
    )

    message = target.message if isinstance(target, types.CallbackQuery) else target

    # --- CASE 1: Message ---
    if isinstance(target, types.Message):
        await target.answer(text, reply_markup=keyboard)
        return

    # --- CASE 2: CallbackQuery ---
    try:
        # если сообщение текстовое → редактируем текст
        await message.edit_text(text, reply_markup=keyboard)
    except TelegramBadRequest:
        # если это photo/video/media → fallback
        await message.delete()
        await message.answer(text, reply_markup=keyboard, )

    await target.answer()


@router_start.callback_query(F.data.startswith("select_lottery_"))
async def process_select_lottery(callback: types.CallbackQuery):
    lottery_id = int(callback.data.split("_")[-1])
    lottery = await LotteryService.get_lottery(lottery_id)
    print(lottery_id, type(lottery_id), lottery)
    if not lottery:
        await callback.answer("⚠️ Эта лотерея уже завершена или не найдена!", show_alert=True)
        await callback.message.delete()
        return

    available_tickets = lottery.total_tickets - lottery.sold_tickets

    if available_tickets <= 0:
        await callback.answer("🎉 Все билеты в этой лотерее распроданы!", show_alert=True)
        return

    await callback.message.edit_media(
        media=InputMediaPhoto(
            media=lottery.photo_file_id,
            caption=(
                f"🎁 <b>Лотерея #{lottery.id}</b>\n\n"
                f"🏆 Приз: {lottery.prize}\n"
                f"💰 Цена билета: {lottery.ticket_price} ⭐️\n"
                f"📊 Продано: {lottery.sold_tickets} из {lottery.total_tickets}\n\n"
                f"Выберите количество билетов:"
            ),
        ),
        reply_markup=get_ticket_quantity_keyboard(
            lottery.id,
            available_tickets
        )
    )
    await callback.answer()


# 4. Покупка (обновлена для безопасности по ID)
@router_start.callback_query(F.data.startswith("buy_ticket_"))
async def process_buy_quantity(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    lottery_id = int(parts[2])
    quantity = int(parts[3])

    lottery = await LotteryService.get_lottery(lottery_id)

    if not lottery:
        await callback.answer("⚠️ Эта лотерея уже завершена!", show_alert=True)
        await callback.message.delete()
        return

    total_price = lottery.ticket_price * quantity

    # Обновляем текст сообщения, добавляя итоговую сумму
    await callback.message.edit_text(
        f"🎁 <b>Лотерея #{lottery.id}</b>\n\n"
        f"🏆 Приз: {lottery.prize}\n"
        f"🎫 Выбрано билетов: {quantity} шт.\n"
        f"💰 Цена за 1 билет: {lottery.ticket_price}₽\n"
        f"💵 <b>Итого к оплате: {total_price}₽</b>\n\n",
        reply_markup=last_keyboard_buy(quantity, lottery.id)
    )
    await callback.answer()


@router_start.callback_query(F.data.startswith("pay_stars_lottery_"))
async def process_pay_stars(callback: types.CallbackQuery):
    # payload: pay_stars_lottery_{user_id}_{quantity}
    parts = callback.data.split("_")
    user_id = int(parts[3])
    total_price = int(parts[4])
    stars = round(total_price * 0.9)

    invoice_payload = f"lottery_{user_id}_{total_price}"

    await callback.message.delete()
    await callback.message.answer_invoice(
        title=f"Пополнение баланса на {total_price}₽",
        description=f"Баланс можете потратить на покупку билета(-ов)",
        payload=invoice_payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Итого", amount=stars)]
    )


@router_start.callback_query(F.data.startswith("pay_cryptobot_lottery_"))
async def process_pay_cryptobot(callback: types.CallbackQuery):
    await callback.answer("⏳ Генерируем ссылку на оплату...", show_alert=False)

    parts = callback.data.split("_")
    user_id = int(parts[3])
    total_price_rubles = int(parts[4])
    usd_rate  = await get_rate("USD")
    total_price = round(total_price_rubles / usd_rate.price, 2)

    invoice_payload = f"lottery_{user_id}_{total_price_rubles}"

    # Запрашиваем ссылку у CryptoBot
    payment_link = await create_cryptobot_invoice(
        lottery_prize=f"Пополнение баланса на {total_price_rubles}",
        total_price=total_price,
        payload=invoice_payload,
        rate=usd_rate.price
    )

    if payment_link:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="💳 Оплатить сейчас", url=payment_link)],
        ])

        kb.inline_keyboard.extend(
            inline_exit_to_payment_method().inline_keyboard
        )

        await callback.message.edit_text(
            f"💎 <b>Оплата через CryptoBot</b>\n\n"
            f"К оплате: {total_price} USDT\n\n"
            f"Нажмите на кнопку ниже, чтобы перейти к безопасной оплате. "
            f"После оплаты бот автоматически выдаст вам билеты.",
            reply_markup=kb
        )
    else:
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании платежа. Попробуйте выбрать другой способ оплаты или обратитесь к админу."
        )

# 5. Успешная оплата (также обновлена для работы с ID)
@router_start.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    try:
        payload = pre_checkout_q.invoice_payload
        parts = payload.split("_")

        # ожидаем:
        # lottery_{user_id}_{total_price_rubles}
        if len(parts) != 3 or parts[0] != "lottery":
            await pre_checkout_q.answer(
                ok=False,
                error_message="⚠️ Некорректные данные платежа."
            )
            return

        user_id = int(parts[1])

        # защита от подмены пользователя
        if pre_checkout_q.from_user.id != user_id:
            await pre_checkout_q.answer(
                ok=False,
                error_message="⚠️ Несоответствие пользователя платежа."
            )
            return

        await pre_checkout_q.answer(ok=True)

    except Exception as e:
        logger.exception(e)
        await pre_checkout_q.answer(
            ok=False,
            error_message="⚠️ Ошибка обработки платежа."
        )


@router_start.message(F.successful_payment)
async def on_successful_payment(message: types.Message):
    # ожидаем:
    # lottery_{user_id}_{total_price_rubles}
    payload = message.successful_payment.invoice_payload
    parts = payload.split("_")
    user_id = int(parts[1])
    quantity = parts[2]

    success = await UserService.add_balance(user_id, Decimal(quantity))

    if success:
        await message.answer(f"⭐ Оплата прошла успешно! Ваш баланс пополнен на {quantity}р. Удачи в розыгрышах! 🍀")


@router_start.callback_query(F.data.startswith("pay_lavatop_lottery_"))
async def process_pay_stars(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    print(parts)
    user_id = int(parts[3])
    quantity = int(parts[4])
    await callback.answer(f"⏳ Генерируем ссылку на оплату... {quantity} Рубчиков", show_alert=False)



    # lottery = await LotteryService.get_lottery(lottery_id)
    # if not lottery:
    #     await callback.answer("Лотерея не найдена", show_alert=True)
    #     return

    # total_price = lottery['ticket_price'] * quantity
    # invoice_payload = f"lottery_{user_id}_{lottery_id}_{quantity}"
    # LINK = "https://gate.lava.top/api/v3/invoice"
    # r = requests.post(LINK, data={
    #     "email": "client@gmail.com",
    #     "offerId": "836b9fc5-7ae9-4a27-9642-592bc44072b7",
    #     "currency": "RUB"
    # })
    # r.raise_for_status()


    payment = client.create_one_time_payment(
        email="orion4605@gmail.com",
        offer_id="836b9fc5-7ae9-4a27-9642-592bc44072b7",
        currency=Currency.RUB,
        payment_method=PaymentMethod.BANK131,
    )
    await callback.message.answer(f"{payment.id=}\n{payment.paymentUrl=}")

# 6. Кнопка "Назад к списку" (опционально, можно добавить в клавиатуру количества билетов)
@router_start.callback_query(F.data == "cancel_buy")
async def cancel_buy(callback: types.CallbackQuery):
    await callback.answer("Покупка отменена", show_alert=False)
    await show_lotteries_list(callback)  # Возвращаем пользователя к списку