# handlers/payment_handler.py
import logging

from aiogram import Bot
from tortoise.transactions import in_transaction

from database.service.user import UserService

logger = logging.getLogger(__name__)


async def process_successful_payment(bot: Bot, metadata: dict):
    """
    Обрабатывает успешную оплату, пришедшую через CryptoBot Webhook.
    """
    try:
        user_id = metadata["user_id"]
        quantity = metadata["quantity"]

        logger.info(f"Processing payment for user {user_id}, qty {quantity}")

        async with in_transaction():
            await UserService.add_balance(user_id, quantity)

        # 1. Уведомляем пользователя
        await bot.send_message(
            chat_id=user_id,
            text=f"✅ Оплата через CryptoBot прошла успешно!\n"
                 f"Ваш баланс пополнен на {quantity}. Удачи в розыгрышах! 🍀"
        )

    except Exception as e:
        logger.error(f"Critical error in process_successful_payment: {e}", exc_info=True)