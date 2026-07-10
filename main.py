import asyncio
import threading

from bot import main as bot_main
from config import init_config, get_config
from crypto_bot.webhook import app as flask_app


def run_flask():
    print("MAIN FLASK INSTANCE:", id(flask_app))
    flask_app.run(host="0.0.0.0", port=5000)



if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--proxy", action="store_true")
    args = parser.parse_args()

    init_config(debug=args.debug, proxy=args.proxy)

    # ❗ 1. Flask в фоне
    threading.Thread(target=run_flask).start()

    # ❗ 2. AIogram В MAIN THREAD (ВАЖНО)
    config = get_config()
    asyncio.run(bot_main(config))