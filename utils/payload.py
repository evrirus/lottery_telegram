# utils/payload.py

import json
from typing import Any

from aiogram.utils.payload import encode_payload, decode_payload

from enum import Enum


class PayloadKey(str, Enum):
    REFERRER_ID = "r"
    LOTTERY_ID = "l"

def create_payload(data: dict[str, Any]) -> str:
    """
    Создает deep-link payload.

    :param data: Данные для передачи через /start
    :return: Закодированный payload
    """

    return encode_payload(
        json.dumps(data, separators=(",", ":"))
    )

def get_payload(payload: str) -> dict[str, Any]:
    """
    Декодирует deep-link payload.

    :param payload: command.args из /start
    """

    try:
        return json.loads(
            decode_payload(payload)
        )
    except (ValueError, json.JSONDecodeError):
        return {}