import asyncio
import logging

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import get_config, init_config, create_session, Config
from database.models import init_db
from handlers.start import router_start
from handlers.admin.create_lottery import router as create_lottery_router
from handlers.admin.refund import router as refund_router

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
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    init_config(debug=args.debug)
    config = get_config()
    asyncio.run(main(config))