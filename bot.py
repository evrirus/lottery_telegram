import asyncio
import logging

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import utils.shared_state as shared_state
from config import create_session
from database.models import init_tortoise
from handlers.admin.create_lottery import router as create_lottery_router
from handlers.admin.refund import router as refund_router
from handlers.inline_mode.referral import router as referral_router
from handlers.my_tickets import router as my_tickets_router
from handlers.replenish import router as replenish_router
from handlers.start import router_start


async def main(config):
    logging.basicConfig(level=logging.INFO)

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=create_session(),
        storage=MemoryStorage()
    )

    dp = Dispatcher()

    dp.include_routers(
        router_start,
        create_lottery_router,
        refund_router,
        replenish_router,
        referral_router,
        my_tickets_router
    )

    await init_tortoise()

    # 🔥 CRITICAL SECTION
    shared_state.BOT = bot
    shared_state.EVENT_LOOP = asyncio.get_running_loop()
    shared_state.READY = True

    print("Bot started")

    await dp.start_polling(bot)