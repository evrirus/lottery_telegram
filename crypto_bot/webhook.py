# webhook.py (ваш файл с Flask)
import asyncio
import logging

import dotenv
from aiosend.types import Invoice
from flask import request

from config import init_config, get_config
from crypto_bot.client import cp, app
from database.service.user import UserService
from handlers.payment_handler import process_successful_payment
from utils import shared_state

dotenv.load_dotenv()
logger = logging.getLogger(__name__)


@cp.invoice_paid()
async def handle_payment(invoice: Invoice):
    logger.info("CryptoPay webhook received")
    logger.info(invoice.model_dump())
    try:
        logger.info(
            f"Payment success: {invoice.amount} {invoice.invoice_id}")
        logger.debug(invoice)
        if not shared_state.READY:
            return

        asyncio.run_coroutine_threadsafe(
            process_successful_payment(shared_state.BOT, str(invoice.invoice_id)),
            shared_state.EVENT_LOOP
        )
        logger.info("invoice_paid event received")
        logger.info(invoice.model_dump())

    except Exception as e:
        logger.error(e, exc_info=True)


@app.route("/lavatop-webhook", methods=["POST"])
def webhook_lavatop():
    try:
        print(request.headers)
        api_key = request.headers.get("X-Api-Key")

        if not api_key:
            return "Missing API key", 401

        config = get_config()
        if api_key != config.LAVATOP_TOKEN:
            return "Invalid API key", 403

        data = request.get_json(silent=True)

        if not data:
            return "OK", 200

        # проверка события
        if data.get("eventType") != "payment.success" or data.get("status") != "completed":
            return "OK", 200

        product = data.get("product", {})
        buyer = data.get("buyer", {})

        contract_id = data.get("contractId")
        amount = data.get("amount")
        currency = data.get("currency")
        telegram_id = data.get("clientUtm", {}).get("telegram_id")

        logger.info(
            f"Payment success: contract={contract_id}, "
            f"amount={amount} {currency}, "
            f"user={buyer.get('email')}, "
            f"product={product.get('id')}, "
            f"telegram_id={telegram_id}"
        )
        bot = shared_state.BOT
        loop = shared_state.EVENT_LOOP
        asyncio.run_coroutine_threadsafe(
            process_successful_payment(bot, contract_id),
            loop
        )

        UserService.add_balance(telegram_id=telegram_id,
                                amount=amount)

        return "OK", 200

    except Exception as e:
        logger.error(f"LavaTop webhook error: {e}", exc_info=True)
        return "OK", 200

@app.before_request
def log_requests():
    print("REQUEST:", request.method, request.path)

if __name__ == '__main__':
    init_config(debug=False)
    app.run(host='0.0.0.0', port=5000, debug=True)