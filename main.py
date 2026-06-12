import threading
import asyncio

from config import init_config, get_config
from crypto_bot.webhook import app as flask_app
from bot import main as bot_main


def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)


def run_bot():
    config = get_config()
    asyncio.run(bot_main(config))


if __name__ == "__main__":
    init_config(debug=False)

    # ❗ 1. bot сначала (ВАЖНО)
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # ❗ 2. Flask после (или можно тоже позже)
    run_flask()