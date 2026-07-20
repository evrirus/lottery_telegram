import logging
import uuid
from decimal import Decimal

import aiohttp
from aiogram import Router, types, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import LabeledPrice, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, InputMediaPhoto
from async_cb_rate.parser import get_rate

from config import get_config
from database.models import Transaction, PaymentProvider
from database.service.lottery import LotteryService
from database.service.transaction import TransactionService
from database.service.user import UserService
from keyboards.inline import get_ticket_quantity_keyboard, get_active_lotteries_keyboard, start_keyboard, \
    last_keyboard_buy, inline_exit_to_payment_method
from service.cryptobot import create_cryptobot_invoice
from utils.payload import get_payload, PayloadKey
from utils.show_lottery import show_lottery

logger = logging.getLogger()
router_start = Router()


@router_start.message(CommandStart(
    deep_link=True,
    deep_link_encoded=True
))
async def cmd_start(message: types.Message, command: CommandObject):
    payload = get_payload(command.args)

    referrer_id = payload.get(PayloadKey.REFERRER_ID)
    referrer_id = int(referrer_id) if referrer_id else None
    _, registered = await UserService.register(message.from_user.id, referrer_id=referrer_id)

    if payload.get(PayloadKey.LOTTERY_ID):
        lottery_id = int(payload.get(PayloadKey.LOTTERY_ID, 0))

        if lottery_id:
            return await show_lottery(
            bot=message.bot,
            user_id=message.from_user.id,
            message=message,
            lottery_id=lottery_id
        )

    text = "🎟 Главное меню 👇"
    if registered:
        text = "Мы рады вас приветствовать!\n\n" + text

    await message.answer(
        text,
        reply_markup=start_keyboard()
    )

@router_start.message(CommandStart())
async def cmd_start(message: types.Message):
    _, registered = await UserService.register(message.from_user.id)

    text = "🎟 Главное меню 👇"
    if registered:
        text = "Мы рады вас приветствовать!\n\n" + text

    await message.answer(
        text,
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

    text = (
        f"🎁 <b>Лотерея #{lottery.id}</b>\n\n"
        f"🏆 Приз: {lottery.prize}\n"
        f"💰 Цена билета: {lottery.ticket_price_display} ⭐️\n"
        f"📊 Продано: {lottery.sold_tickets} из {lottery.total_tickets}\n\n"
        f"Выберите количество билетов:"
    )

    markup = get_ticket_quantity_keyboard(
        lottery.id,
        available_tickets
    )

    if lottery.photo_file_id:
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=lottery.photo_file_id,
                caption=text,
            ),
            reply_markup=markup
        )
    else:
        await callback.message.edit_text(
            text=text,
            reply_markup=markup
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

    text = (f"🎁 <b>Лотерея #{lottery.id}</b>\n\n"
        f"🏆 Приз: {lottery.prize}\n"
        f"🎫 Выбрано билетов: {quantity} шт.\n"
        f"💰 Цена за 1 билет: {lottery.ticket_price}₽\n\n"
        f"💵 <b>Итого к оплате: {total_price}₽</b>")
    markup = last_keyboard_buy(quantity, lottery.id)

    if lottery.photo_file_id:
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=lottery.photo_file_id,
                caption=text,
            ),
            reply_markup=markup
        )
    else:
        await callback.message.edit_text(
            text=text,
            reply_markup=markup
        )
    await callback.answer()



@router_start.callback_query(F.data.startswith("pay_stars_"))
async def process_pay_stars(callback: types.CallbackQuery):
    # payload: pay_stars_{quantity}
    parts = callback.data.split("_")

    total_price = int(parts[2])
    rate = 0.9
    stars = round(total_price * rate)

    payment_id = str(uuid.uuid4())

    user = await UserService.get_user(callback.from_user.id)
    await TransactionService.create_transaction(
        external_payment_id=payment_id,
        user=user,
        amount=Decimal(str(total_price)),
        provider=PaymentProvider.TELEGRAM_STARS,
        metadata={
            "stars_amount": stars,
            "rate": rate
        }
    )

    await callback.message.delete()
    await callback.message.answer_invoice(
        title=f"Пополнение баланса на {total_price}₽",
        description=f"Баланс можете потратить на покупку билета(-ов)",
        payload=payment_id,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Итого", amount=stars)]
    )


@router_start.callback_query(F.data.startswith("pay_cryptobot_"))
async def process_pay_cryptobot(callback: types.CallbackQuery):
    await callback.answer("⏳ Генерируем ссылку на оплату...", show_alert=False)

    parts = callback.data.split("_")
    total_price_rubles = int(parts[2])
    usd_rate = await get_rate("USD")
    total_price = round(total_price_rubles / usd_rate.price, 2)

    payment_id = str(uuid.uuid4())

    user = await UserService.get_user(callback.from_user.id)

    # Запрашиваем ссылку у CryptoBot
    invoice = await create_cryptobot_invoice(
        lottery_prize=f"Баланс будет пополнен на {total_price_rubles}₽",
        total_price=total_price,
        payload=payment_id,
        rate=usd_rate.price
    )
    payment_link = invoice.bot_invoice_url
    await TransactionService.create_transaction(
        external_payment_id=str(invoice.invoice_id),
        user=user,
        amount=Decimal(str(total_price_rubles)),
        provider=PaymentProvider.CRYPTOBOT,
        metadata={
            "usd_amount": usd_rate.price,
            "total_price": total_price,
            "payment_link": payment_link
        }
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
        payment_id = pre_checkout_q.invoice_payload
        transaction = await TransactionService.get_transaction(payment_id)

        # защита от подмены пользователя
        if pre_checkout_q.from_user.id != transaction.user.telegram_id:
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
    payment_id = message.successful_payment.invoice_payload
    transaction = await TransactionService.get_transaction(payment_id)

    success = await UserService.add_balance(
        transaction.user.telegram_id,
        transaction.amount
    )
    if success:
        await message.answer(f"⭐ Оплата прошла успешно! Ваш баланс пополнен на {transaction.amount}р. Удачи в розыгрышах! 🍀")


@router_start.callback_query(F.data.startswith("pay_sbp_"))
async def process_pay_stars(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    print(parts)
    quantity = int(parts[2])
    await callback.answer(f"⏳ Генерируем ссылку на оплату... {quantity} Рубчиков")

    config = get_config()
    payload = {
        "email": "client@lava.top",
        "offerId": config.LAVATOP_OFFER_ID,
        "currency": "RUB",
        "clientUtm": {
            "telegram_id": callback.from_user.id
        },
        "amount": quantity,
        "paymentMethod": "SBP",
        "paymentProvider": "PAY2ME"
    }

    headers = {
        "X-Api-Key": config.LAVATOP_TOKEN,
        "Accept": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
                "https://gate.lava.top/api/v3/invoice",
                json=payload,
                headers=headers
        ) as response:
            text = await response.text()

            if response.status not in (200, 201):
                raise Exception(text)

            invoice = await response.json(content_type=None)

    payment_url = invoice.get("paymentUrl")
    payment_id = invoice.get("id")

    user = await UserService.get_user(callback.from_user.id)
    await Transaction.create(
        external_payment_id=payment_id,
        user=user,
        amount=quantity,
        provider=PaymentProvider.LAVA_SBP,
        metadata={
            "payment_url": payment_url,
            "method": "SBP"
        }
    )
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💳 Оплатить сейчас", url=payment_url)],
    ])

    kb.inline_keyboard.extend(
        inline_exit_to_payment_method().inline_keyboard
    )
    await callback.message.edit_text(
        f"💎 <b>Оплата через СБП</b>\n\n"
        f"К оплате: {quantity} RUB\n\n"
        f"Нажмите на кнопку ниже, чтобы перейти к безопасной оплате. "
        f"После оплаты бот автоматически выдаст вам билеты.",
        reply_markup=kb
    )

# 6. Кнопка "Назад к списку" (опционально, можно добавить в клавиатуру количества билетов)
@router_start.callback_query(F.data == "cancel_buy")
async def cancel_buy(callback: types.CallbackQuery):
    await callback.answer("Покупка отменена", show_alert=False)
    await show_lotteries_list(callback)  # Возвращаем пользователя к списку