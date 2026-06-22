# webhook.py (ваш файл с Flask)
import asyncio
import logging

from async_cb_rate.parser import get_rate
from flask import Flask, request

from config import init_config, get_config
from crypto_bot.verify import verify_crypto_pay_signature
from handlers.payment_handler import process_successful_payment
from utils import shared_state

logger = logging.getLogger(__name__)
app = Flask(__name__)


@app.route("/cryptobot-webhook", methods=["POST"])
def webhook_cryptobot():
    try:
        config = get_config()
        verify = verify_crypto_pay_signature(config.CRYPTOBOT_TOKEN, request=request)
        print(f"verify: {verify}")
        if not verify:
            return "invalid signature", 403

        data = request.get_json(silent=True)

        if not data:
            return "OK", 200

        if not shared_state.READY:
            logger.error("System not ready yet")
            return "OK", 200

        bot = shared_state.BOT
        loop = shared_state.EVENT_LOOP

        if bot is None or loop is None:
            logger.error("Bot/loop missing")
            return "OK", 200

        if not loop.is_running():
            logger.error("Loop not running")
            return "OK", 200

        payload = data.get("payload", {}).get("payload")
        if not payload:
            return "OK", 200

        parts = payload.split("_")
        print(parts)
        if len(parts) != 3:
            return "OK", 200

        metadata = {
            "user_id": int(parts[1]),
            "quantity": int(parts[2])
        }

        asyncio.run_coroutine_threadsafe(
            process_successful_payment(bot, metadata),
            loop
        )

        return "OK", 200

    except Exception as e:
        logger.error(e, exc_info=True)
        return "OK", 200



@app.route("/lavatop-webhook", methods=["POST"])
def webhook_lavatop():
    try:
        print(request.headers)
        api_key = request.headers.get("X-Api-Key")

        if not api_key:
            return "Missing API key", 401

        if api_key != "YOUR_SECRET_KEY":
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

        logger.info(
            f"Payment success: contract={contract_id}, "
            f"amount={amount} {currency}, "
            f"user={buyer.get('email')}, "
            f"product={product.get('id')}"
        )


        # ⚠️ здесь твоя бизнес-логика
        # например:
        # user_id = find_user_by_email(buyer["email"])
        # add_balance(user_id, Decimal(str(amount)))

        return "OK", 200

    except Exception as e:
        logger.error(f"LavaTop webhook error: {e}", exc_info=True)
        return "OK", 200

if __name__ == '__main__':
    init_config(debug=False)
    app.run(host='0.0.0.0', port=5000, debug=True)