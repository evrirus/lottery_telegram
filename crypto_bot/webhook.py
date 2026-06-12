# webhook.py (ваш файл с Flask)
import asyncio
import logging

from flask import Flask, request, current_app

from config import get_config, init_config
from handlers.payment_handler import process_successful_payment
from utils import shared_state

logger = logging.getLogger(__name__)
app = Flask(__name__)


@app.route("/cryptobot-webhook", methods=["POST"])
def cryptobot_webhook_handler():
    try:
        data = request.get_json(silent=True)

        if not data:
            return "OK", 200

        if data.get("update_type") != "invoice_paid":
            return "OK", 200

        payload = data.get("payload", {}).get("payload")

        if not payload:
            logger.warning("Empty payload")
            return "OK", 200

        parts = payload.split("_")

        if len(parts) != 4 or parts[0] != "lottery":
            logger.error(f"Bad payload: {payload}")
            return "Error", 400

        user_id = int(parts[1])
        lottery_id = int(parts[2])
        quantity = int(parts[3])

        metadata = {
            "user_id": user_id,
            "lottery_id": lottery_id,
            "quantity": quantity,
        }

        bot = shared_state.BOT
        loop = shared_state.EVENT_LOOP

        # 🔥 HARD SAFETY CHECK
        if bot is None or loop is None:
            logger.error("Bot or loop not initialized yet")
            return "OK", 200

        if not loop.is_running():
            logger.error("Event loop is not running")
            return "OK", 200

        asyncio.run_coroutine_threadsafe(
            process_successful_payment(bot, metadata),
            loop,
        )

        return "OK", 200

    except Exception as e:
        logger.error(f"Webhook error: {e}", exc_info=True)
        return "Error", 500


if __name__ == '__main__':
    init_config(debug=False)
    app.run(host='0.0.0.0', port=5000, debug=True)