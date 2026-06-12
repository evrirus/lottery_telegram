import asyncio
from typing import Optional
from aiogram import Bot

EVENT_LOOP: Optional[asyncio.AbstractEventLoop] = None
BOT: Optional[Bot] = None

READY: bool = False