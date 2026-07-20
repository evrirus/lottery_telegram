# utils/payload.py

import json
from enum import Enum
from typing import Any

from aiogram.utils.payload import encode_payload


class PayloadKey(str, Enum):
    REFERRER_ID = "r"
    LOTTERY_ID = "l"
    COMMAND = "c"

class StartCommand(str, Enum):
    REPLENISH = "r"


def create_payload(data: dict[PayloadKey, Any]) -> str:
    """
    Создает deep-link payload.

    :param data: Данные для передачи через /start
    :return: Закодированный payload
    """

    return encode_payload(
        json.dumps(data, separators=(",", ":"))
    )

def get_payload(payload: str) -> dict[PayloadKey, Any]:
    try:
        data = json.loads(payload)

        return {
            PayloadKey(key): value
            for key, value in data.items()
        }

    except (ValueError, json.JSONDecodeError):
        return {}