# webhook.py (ваш файл с Flask)
import asyncio
import logging

from flask import Flask, request, current_app

from config import get_config, init_config
from handlers.payment_handler import process_successful_payment

logger = logging.getLogger(__name__)
app = Flask(__name__)


@app.route('/cryptobot-webhook', methods=['POST'])
def cryptobot_webhook_handler():
    try:
        request_data = request.get_json(silent=True)

        print(request_data)
        print(request_data.get('update_type'))
        # CryptoBot отправляет update_type == "invoice_paid" при успешной оплате
        if request_data and request_data.get('update_type') == 'invoice_paid':
            # В CryptoBot полезная нагрузка часто лежит внутри ключа 'payload'
            payload_string = request_data.get('payload', {}).get('payload')

            if not payload_string:
                logger.warning("CryptoBot Webhook: Received paid invoice but payload was empty.")
                return 'OK', 200

            # Парсим формат: "lottery_{user_id}_{lottery_id}_{quantity}"
            parts = payload_string.split('_')

            if len(parts) != 4 or parts[0] != 'lottery':
                logger.error(f"CryptoBot Webhook: Invalid payload format received: {payload_string}")
                return 'Error', 400

            user_id = int(parts[1])
            lottery_id = int(parts[2])
            quantity = int(parts[3])

            metadata = {
                "user_id": user_id,
                "lottery_id": lottery_id,
                "quantity": quantity
            }

            config = get_config()
            bot = config.BOT

            loop = current_app.config.get('EVENT_LOOP')

            # Импортируем функцию здесь, чтобы избежать циклических импортов
            print("process_successful_payment")

            if bot and loop and loop.is_running():
                # Передаем задачу в основной asyncio-цикл бота
                asyncio.run_coroutine_threadsafe(process_successful_payment(bot, metadata), loop)
            else:
                logger.error("CryptoBot Webhook: Bot or event loop is not running.")

        return 'OK', 200

    except Exception as e:
        logger.error(f"Error in cryptobot webhook handler: {e}", exc_info=True)
        return 'Error', 500


if __name__ == '__main__':
    init_config(debug=False)
    app.run(host='0.0.0.0', port=5000, debug=True)