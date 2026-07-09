# handlers/payment_handler.py
import logging

from aiogram import Bot

from database.service.transaction import TransactionService
from database.service.user import UserService

logger = logging.getLogger(__name__)


async def process_successful_payment(bot: Bot, payment_id: str):
    """
    Обрабатывает успешную оплату, пришедшую через CryptoBot Webhook.
    """
    try:
        transaction = await TransactionService.get_transaction(payment_id)
        if not transaction:
            logger.error(f"Critical error in process_successful_payment: {payment_id}", exc_info=True)
            return False

        await TransactionService.complete_transaction(payment_id)
        await UserService.add_balance(
            transaction.user.telegram_id,
            transaction.amount
        )

        # 1. Уведомляем пользователя
        await bot.send_message(
            chat_id=transaction.user.telegram_id,
            text=f"✅ Оплата через CryptoBot прошла успешно!\n"
                 f"Ваш баланс пополнен на {transaction.amount}р. Удачи в розыгрышах! 🍀"
        )

    except Exception as e:
        logger.error(f"Critical error in process_successful_payment: {e}", exc_info=True)