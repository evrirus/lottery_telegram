# services/cryptobot.py
import logging

from aiosend import CryptoPay, TESTNET
from aiosend.types.invoice import Invoice

from config import get_config  # Убедитесь, что у вас есть функция получения конфига

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
    config = get_config()

    cp = CryptoPay(
        token=config.CRYPTOBOT_TOKEN,
        network=TESTNET,
    )

    return await cp.create_invoice(
        amount=total_price,
        asset="USDT",
        description=lottery_prize,
        payload=payload,
        allow_comments=False,
        allow_anonymous=False
    )
