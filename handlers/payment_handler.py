# handlers/payment_handler.py
import logging
from aiogram import Bot
from database.models import buy_ticket
from service.lottery_logic import check_and_announce_winner

logger = logging.getLogger(__name__)


async def process_successful_payment(bot: Bot, metadata: dict):
    """
    Обрабатывает успешную оплату, пришедшую через CryptoBot Webhook.
    """
    try:
        user_id = metadata["user_id"]
        lottery_id = metadata["lottery_id"]
        quantity = metadata["quantity"]

        logger.info(f"Processing payment for user {user_id}, lottery {lottery_id}, qty {quantity}")

        # Пытаемся выдать билеты (внутри buy_ticket есть защита BEGIN IMMEDIATE от гонки данных)
        success = await buy_ticket(lottery_id, user_id, quantity)

        if success:
            # 1. Уведомляем пользователя
            await bot.send_message(
                chat_id=user_id,
                text=f"✅ Оплата через CryptoBot прошла успешно!\n"
                     f"Вы купили {quantity} билет(ов). Удачи в розыгрыше! 🍀"
            )

            # 2. Проверяем, не стал ли этот покупатель тем, кто выкупил последний билет
            await check_and_announce_winner(lottery_id)

        else:
            # Этот блок сработает ТОЛЬКО в случае редкой гонки данных (race condition),
            # когда на момент вебхука билеты уже закончились.
            logger.warning(f"Failed to issue tickets for user {user_id}. Likely sold out at the last millisecond.")
            await bot.send_message(
                chat_id=user_id,
                text="❌ К сожалению, в момент подтверждения оплаты последние билеты были выкуплены другим пользователем. "
                     "Пожалуйста, обратитесь в поддержку для возврата средств."
            )

    except Exception as e:
        logger.error(f"Critical error in process_successful_payment: {e}", exc_info=True)