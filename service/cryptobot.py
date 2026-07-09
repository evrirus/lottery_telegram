# services/cryptobot.py
import logging

from aiosend.types.invoice import Invoice

from crypto_bot.client import cp

logger = logging.getLogger(__name__)


async def create_cryptobot_invoice(
        lottery_prize: str,
        total_price: float,
        payload: str,
        rate: float,
) -> Invoice:
    """
    Создает инвойс в CryptoBot и возвращает ссылку на оплату.
    """

    return await cp.create_invoice(
        amount=total_price,
        asset="USDT",
        description=lottery_prize,
        payload=payload,
        allow_comments=False,
        allow_anonymous=False
    )
