# webhook.py (ваш файл с Flask)
import asyncio
import logging

from aiogram.types import Message
from aiosend import CryptoPay
from aiosend.types import Invoice
from aiosend.webhook import FlaskManager
from flask import Flask, request

from config import init_config, get_config
from database.service.user import UserService
from handlers.payment_handler import process_successful_payment
from utils import shared_state

logger = logging.getLogger(__name__)
app = Flask(__name__)
cp = CryptoPay(
    "TOKEN",
    webhook_manager=FlaskManager(app, "/cryptobot-webhook"),
)

@cp.invoice_paid()
async def handle_payment(invoice: Invoice, message: Message):
    print(type(invoice), type(message))
    await message.answer(
        f"invoice #{invoice.invoice_id} paid"
    )
    try:
        payment_id = invoice.payload
        if not payment_id:
            return

        loop = shared_state.EVENT_LOOP
        if not shared_state.READY:
            return

        asyncio.run_coroutine_threadsafe(
            process_successful_payment(message.bot, payment_id),
            loop
        )

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

if __name__ == '__main__':
    init_config(debug=False)
    app.run(host='0.0.0.0', port=5000, debug=True)