import asyncio
import logging
import threading

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import get_config, init_config, create_session, Config
from database.models import init_db
from handlers.start import router_start
from handlers.admin.create_lottery import router as create_lottery_router
from handlers.admin.refund import router as refund_router
from crypto_bot.webhook import app as flask_app

def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)

async def main(config: Config):
    logging.basicConfig(level=logging.INFO)

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=create_session(),
        storage=MemoryStorage()
    )
    config.set_bot(bot)

    await init_db()
    dp = Dispatcher()

    # routers
    dp.include_routers(
        router_start,
        create_lottery_router,
        refund_router,
    )

    print("Bot started...")

    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    init_config(debug=args.debug)
    config = get_config()

    # Flask в фоне
    threading.Thread(target=run_flask, daemon=True).start()

    # aiogram основной поток
    asyncio.run(main(config))