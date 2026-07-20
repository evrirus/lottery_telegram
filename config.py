import os
from dataclasses import dataclass
from typing import Optional

from aiogram import Bot
from aiogram.client.session.aiohttp import AiohttpSession
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    debug: bool

    BOT_TOKEN: str
    # PRIVATE_CHANNEL_ID: int
    ADMIN_ID: int

    CHANNEL_ID: Optional[int] = None
    proxy: Optional[str] = None
    BOT: Optional[Bot] = None
    CRYPTOBOT_TOKEN: Optional[str] = None
    LAVATOP_TOKEN: Optional[str] = None
    LAVATOP_OFFER_ID: Optional[str] = None

    def set_bot(self, bot: Bot) -> None:
        self.BOT = bot

_config: Optional[Config] = None


def init_config(debug: bool, proxy: bool = False) -> None:
    global _config

    def env(name: str, required=True) -> str:
        value = os.getenv(name)
        if required and not value:
            raise RuntimeError(f"Missing env variable: {name}")
        return value

    if debug:
        _config = Config(
            debug=True,
            BOT_TOKEN=env("TOKEN"),
            ADMIN_ID=int(env("ADMIN_ID")),
            proxy="socks5://p8tojo:6hxcrs@45.91.209.134:10034" if proxy else None,
            BOT=None,
            CRYPTOBOT_TOKEN=env("CRYPTOBOT_TOKEN"),
            LAVATOP_TOKEN=env("LAVATOP_TOKEN"),
            LAVATOP_OFFER_ID=env("LAVATOP_OFFER_ID")
        )
    else:
        _config = Config(
            debug=False,
            BOT_TOKEN=env("TOKEN"),
            ADMIN_ID=int(env("ADMIN_ID")),
            proxy="socks5://p8tojo:6hxcrs@45.91.209.134:10034" if proxy else None,
            BOT=None,
            CRYPTOBOT_TOKEN=env("CRYPTOBOT_TOKEN"),
            LAVATOP_TOKEN=env("LAVATOP_TOKEN"),
            LAVATOP_OFFER_ID=env("LAVATOP_OFFER_ID")
        )


def get_config() -> Config:
    if _config is None:
        raise RuntimeError("Config is not initialized. Call init_config() first.")
    return _config


def create_session():
    cfg = get_config()

    if cfg.proxy:
        return AiohttpSession(
            proxy=cfg.proxy,
            timeout=5
        )

    return AiohttpSession(timeout=5)

TORTOISE_ORM = {
    "connections": {
        "default": "postgres://lottery_user:твой_пароль@localhost:5432/lottery"
    },
    "apps": {
        "models": {
            "models": [
                "database.models",
                "aerich.models",
            ],
            "default_connection": "default",
        }
    }
}