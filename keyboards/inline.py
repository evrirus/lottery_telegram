# keyboards/inline.py
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup


def get_ticket_quantity_keyboard(lottery_id: int, available_tickets: int) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру с выбором количества билетов.
    Учитывает остаток билетов, чтобы нельзя было выбрать больше, чем есть.
    """
    builder = InlineKeyboardBuilder()

    # Стандартные варианты покупки
    quantities = [1, 2, 3, 5, 10]

    # Оставляем только те варианты, которые меньше или равны доступному остатку
    valid_quantities = [q for q in quantities if q <= available_tickets]

    # Если вдруг остался 1 билет, а в списке его не было (гипотетически), добавим его
    if not valid_quantities and available_tickets > 0:
        valid_quantities = [available_tickets]

    for qty in valid_quantities:
        builder.button(
            text=f"🎫 {qty} шт.",
            callback_data=f"buy_ticket_{lottery_id}_{qty}"
        )

    # Кнопка отмены
    builder.button(text="❌ Отмена", callback_data="cancel_buy")

    # Выравниваем кнопки: 3 в первом ряду, остальные (2) во втором
    builder.adjust(3, 2)

    return builder.as_markup()


def get_active_lotteries_keyboard(lotteries: list) -> InlineKeyboardMarkup:
    """Генерирует клавиатуру со списком доступных лотерей"""
    builder = InlineKeyboardBuilder()

    for lottery in lotteries:

        available = lottery.total_tickets - lottery.sold_tickets
        if not available:
            continue
        # Обрезаем длинное название приза для красоты кнопки
        prize_short = lottery['prize'][:25] + "..." if len(lottery.prize) > 25 else lottery.prize

        builder.button(
            text=f"🎫 {prize_short} ({available} ост.)",
            callback_data=f"select_lottery_{lottery.id}"
        )

    # Выстраиваем по 1 кнопке в ряд для удобства чтения
    builder.adjust(1)
    return builder.as_markup()


# keyboards/inline.py

def get_payment_method_keyboard(user_id: int, amount: int) -> InlineKeyboardMarkup:
    """
    Генерирует клавиатуру с выбором способа оплаты.
    """
    builder = InlineKeyboardBuilder()
    payload = f"lottery_{user_id}_{amount}"

    builder.button(
        text="⭐️ Telegram",
        callback_data=f"pay_stars_{payload}"
    )
    builder.button(
        text="💎 CryptoBot",
        callback_data=f"pay_cryptobot_{payload}"
    )
    builder.button(
        text="🌋 LavaTop",
        callback_data=f"pay_lavatop_{payload}"
    )

    builder.button(text="❌ Отмена", callback_data="cancel_buy")

    # Выстраиваем по 1 кнопке в ряд для удобства нажатия
    builder.adjust(1)

    return builder.as_markup()

def start_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Лотереи",
        callback_data="lotteries"
    )
    builder.button(
        text="Пополнить",
        callback_data="replenish"
    )
    builder.adjust(1, repeat=True)
    return builder.as_markup()


def to_replenish_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    amounts = [100, 300, 500, 1000, 2000, 5000, 7500]

    for amount in amounts:
        builder.button(
            text=f"{amount} ₽",
            callback_data=f"replenish_{amount}"
        )

    builder.button(
        text="❌ Отменить",
        callback_data="lotteries"
    )

    builder.adjust(3, 4, 1)

    return builder.as_markup()

def last_keyboard_buy(qty: int, lottery_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Купить",
        callback_data=f"buy_tickets_{qty}_{lottery_id}"
    )
    return builder.as_markup()