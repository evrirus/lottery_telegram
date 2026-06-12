import logging

from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import LabeledPrice

from database.models import buy_ticket, get_all_active_lotteries, get_lottery_by_id, check_ticket_availability
from keyboards.inline import get_ticket_quantity_keyboard, get_active_lotteries_keyboard, get_payment_method_keyboard
from service.cryptobot import create_cryptobot_invoice
from service.lottery_logic import check_and_announce_winner

logger = logging.getLogger()
router_start = Router()


@router_start.message(CommandStart())
async def cmd_start(message: types.Message):
    await show_lotteries_list(message)

# 2. Новая команда /lotteries
@router_start.message(Command("lotteries"))
async def cmd_lotteries(message: types.Message):
    await show_lotteries_list(message)


async def show_lotteries_list(target: types.Message | types.CallbackQuery):
    """Универсальная функция для показа списка лотерей (работает и для Message, и для CallbackQuery)"""
    lotteries = await get_all_active_lotteries()

    if not lotteries:
        text = "🕊 Сейчас нет активных лотерей. Следите за обновлениями!"
        if isinstance(target, types.Message):
            await target.answer(text)
        else:
            await target.message.edit_text(text)
            await target.answer()  # Снимаем часики загрузки
        return

    text = "📋 <b>Список активных лотерей:</b>\n\nВыберите интересующую вас лотерею:"

    if isinstance(target, types.Message):
        await target.answer(
            text,
            reply_markup=get_active_lotteries_keyboard(lotteries)
        )
    else:
        await target.message.edit_text(
            text,
            reply_markup=get_active_lotteries_keyboard(lotteries)
        )
        await target.answer()


@router_start.callback_query(F.data.startswith("select_lottery_"))
async def process_select_lottery(callback: types.CallbackQuery):
    lottery_id = int(callback.data.split("_")[-1])
    lottery = await get_lottery_by_id(lottery_id)

    if not lottery:
        await callback.answer("⚠️ Эта лотерея уже завершена или не найдена!", show_alert=True)
        await callback.message.delete()
        return

    available_tickets = lottery['total_tickets'] - lottery['sold_tickets']

    if available_tickets <= 0:
        await callback.answer("🎉 Все билеты в этой лотерее распроданы!", show_alert=True)
        return

    await callback.message.edit_text(
        f"🎁 **Лотерея #{lottery['id']}**\n\n"
        f"🏆 Приз: {lottery['prize']}\n"
        f"💰 Цена билета: {lottery['ticket_price']} ⭐️\n"
        f"📊 Продано: {lottery['sold_tickets']} из {lottery['total_tickets']}\n\n"
        f"Выберите количество билетов:",
        parse_mode="Markdown",
        reply_markup=get_ticket_quantity_keyboard(lottery['id'], available_tickets)
    )
    await callback.answer()


# 4. Покупка (обновлена для безопасности по ID)
@router_start.callback_query(F.data.startswith("buy_ticket_"))
async def process_buy_quantity(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    lottery_id = int(parts[2])
    quantity = int(parts[3])

    lottery = await get_lottery_by_id(lottery_id)

    if not lottery:
        await callback.answer("⚠️ Эта лотерея уже завершена!", show_alert=True)
        await callback.message.delete()
        return

    user_id = callback.from_user.id
    total_price = lottery['ticket_price'] * quantity

    # Обновляем текст сообщения, добавляя итоговую сумму
    await callback.message.edit_text(
        f"🎁 **Лотерея #{lottery['id']}**\n\n"
        f"🏆 Приз: {lottery['prize']}\n"
        f"🎫 Выбрано билетов: {quantity} шт.\n"
        f"💰 Цена за 1 билет: {lottery['ticket_price']}\n"
        f"💵 **Итого к оплате: {total_price}**\n\n"
        f"Выберите удобный способ оплаты:",
        parse_mode="Markdown",
        reply_markup=get_payment_method_keyboard(user_id, lottery_id, quantity)
    )
    await callback.answer()


@router_start.callback_query(F.data.startswith("pay_stars_lottery_"))
async def process_pay_stars(callback: types.CallbackQuery):
    # payload: pay_stars_lottery_{user_id}_{lottery_id}_{quantity}
    parts = callback.data.split("_")
    user_id = int(parts[3])
    lottery_id = int(parts[4])
    quantity = int(parts[5])

    lottery = await get_lottery_by_id(lottery_id)
    if not lottery:
        await callback.answer("Лотерея не найдена", show_alert=True)
        return

    total_price = lottery['ticket_price'] * quantity
    invoice_payload = f"lottery_{user_id}_{lottery_id}_{quantity}"

    await callback.message.answer_invoice(
        title=f"Билет: {lottery['prize']}",
        description=f"Количество: {quantity} шт.",
        payload=invoice_payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Итого", amount=total_price)],
    )
    await callback.answer()


@router_start.callback_query(F.data.startswith("pay_cryptobot_lottery_"))
async def process_pay_cryptobot(callback: types.CallbackQuery):
    await callback.answer("⏳ Генерируем ссылку на оплату...", show_alert=False)

    parts = callback.data.split("_")
    user_id = int(parts[3])
    lottery_id = int(parts[4])
    quantity = int(parts[5])

    lottery = await get_lottery_by_id(lottery_id)
    if not lottery:
        await callback.answer("Лотерея не найдена", show_alert=True)
        return

    total_price = lottery['ticket_price'] * quantity
    invoice_payload = f"lottery_{user_id}_{lottery_id}_{quantity}"

    # Запрашиваем ссылку у CryptoBot
    payment_link = await create_cryptobot_invoice(
        user_id=user_id,
        lottery_prize=lottery['prize'],
        quantity=quantity,
        total_price=total_price,
        payload=invoice_payload
    )

    if payment_link:
        await callback.message.edit_text(
            f"💎 **Оплата через CryptoBot**\n\n"
            f"К оплате: {total_price} USDT\n"
            f"Билетов: {quantity} шт.\n\n"
            f"Нажмите на кнопку ниже, чтобы перейти к безопасной оплате. "
            f"После оплаты бот автоматически выдаст вам билеты.",
            parse_mode="Markdown",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="💳 Оплатить сейчас", url=payment_link)]
            ])
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

        # Проверяем, что payload имеет правильный формат "lottery_ID_QTY"
        if len(parts) != 3 or parts[0] != "lottery":
            await pre_checkout_q.answer(
                ok=False,
                error_message="⚠️ Некорректные данные платежа. Попробуйте выбрать билеты заново."
            )
            return

        lottery_id = int(parts[1])
        quantity = int(parts[2])

        # 👇 ПРОВЕРЯЕМ НАЛИЧИЕ БИЛЕТОВ 👇
        is_available = await check_ticket_availability(lottery_id, quantity)

        if is_available:
            # Все ок, разрешаем Telegram списать средства
            await pre_checkout_q.answer(ok=True)
        else:
            # Билетов не хватает. Telegram покажет это сообщение и ОТМЕНИТ оплату.
            await pre_checkout_q.answer(
                ok=False,
                error_message=f"❌ К сожалению, {quantity} билетов только что закончились. Попробуйте купить меньшее количество или выберите другую лотерею."
            )

    except Exception as e:

        logger.exception(str(e))
        await pre_checkout_q.answer(
            ok=False,
            error_message="⚠️ Ошибка обработки данных платежа. Попробуйте снова."
        )

@router_start.message(F.successful_payment)
async def on_successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    parts = payload.split("_")
    lottery_id = int(parts[1])
    quantity = int(parts[2])

    success = await buy_ticket(lottery_id, message.from_user.id, quantity)

    if success:
        await message.answer(f"✅ Оплата прошла! Вы купили {quantity} билет(ов). Удачи! 🍀")
        await check_and_announce_winner(lottery_id)
    else:
        await message.answer("❌ К сожалению, билеты только что закончились. Обратитесь в поддержку.")


# 6. Кнопка "Назад к списку" (опционально, можно добавить в клавиатуру количества билетов)
@router_start.callback_query(F.data == "cancel_buy")
async def cancel_buy(callback: types.CallbackQuery):
    await callback.answer("Покупка отменена", show_alert=False)
    await show_lotteries_list(callback)  # Возвращаем пользователя к списку