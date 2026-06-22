# services/cryptobot.py
import aiohttp
import logging

import aiohttp

from config import get_config  # Убедитесь, что у вас есть функция получения конфига

logger = logging.getLogger(__name__)


async def create_cryptobot_invoice(
        lottery_prize: str,
        total_price: float,
        payload: str,
        rate: float
) -> str | None:
    """
    Создает инвойс в CryptoBot и возвращает ссылку на оплату.
    """
    config = get_config()
    api_token = config.CRYPTOBOT_TOKEN  # Добавьте этот токен в ваш .env

    # url = "https://pay.crypt.bot/api/createInvoice"
    #TODO: расскоментировать
    url = "https://testnet-pay.crypt.bot/api/createInvoice"

    headers = {
        "Crypto-Pay-API-Token": api_token,
        "Content-Type": "application/json"
    }
    print(total_price)
    print(rate)
    print(total_price / rate)
    print(total_price * rate)
    data = {
        "asset": "USDT",  # Или "TON", "BTC" в зависимости от того, что вы принимаете
        "amount": str(total_price),
        "description": lottery_prize,
        "payload": payload,
        "allow_comments": False,
        "allow_anonymous": False
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=data) as response:
                result = await response.json()

                if result.get("ok"):
                    return result["result"]["bot_invoice_url"]
                else:
                    logger.error(f"CryptoBot API Error: {result}")
                    return None
    except Exception as e:
        logger.error(f"Exception during CryptoBot invoice creation: {e}")
        return None