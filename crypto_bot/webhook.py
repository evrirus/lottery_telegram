# webhook.py (ваш файл с Flask)
import asyncio
import logging

from flask import Flask, request

from config import init_config
from handlers.payment_handler import process_successful_payment
from utils import shared_state

logger = logging.getLogger(__name__)
app = Flask(__name__)


@app.route("/cryptobot-webhook", methods=["POST"])
def webhook():
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
        if len(parts) != 4:
            return "OK", 200

        metadata = {
            "user_id": int(parts[1]),
            "lottery_id": int(parts[2]),
            "quantity": int(parts[3]),
        }

        asyncio.run_coroutine_threadsafe(
            process_successful_payment(bot, metadata),
            loop
        )

        return "OK", 200

    except Exception as e:
        logger.error(e, exc_info=True)
        return "OK", 200


if __name__ == '__main__':
    init_config(debug=False)
    app.run(host='0.0.0.0', port=5000, debug=True)