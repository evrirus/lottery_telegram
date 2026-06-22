# webhook.py (ваш файл с Flask)
import asyncio
import logging

from async_cb_rate.parser import get_rate
from flask import Flask, request

from config import init_config
from handlers.payment_handler import process_successful_payment
from utils import shared_state

logger = logging.getLogger(__name__)
app = Flask(__name__)


@app.route("/cryptobot-webhook", methods=["POST"])
def webhook_cryptobot():
    try:
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

        future = asyncio.run_coroutine_threadsafe(get_rate("USD"), loop)
        rate_usd = future.result()

        metadata = {
            "user_id": int(parts[1]),
            "quantity": round(float(parts[2]) * rate_usd.price, 2)
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
    data = request.get_json(silent=True)
    print(data)

    if not data:
        return "OK", 200

if __name__ == '__main__':
    init_config(debug=False)
    app.run(host='0.0.0.0', port=5000, debug=True)