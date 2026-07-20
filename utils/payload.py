import json
from typing import Any
from enum import Enum


class PayloadKey(str, Enum):
    REFERRER_ID = "r"
    LOTTERY_ID = "l"


def create_payload(data: dict[PayloadKey, Any]) -> str:
    prepared_data = {
        key.value if isinstance(key, PayloadKey) else key: value
        for key, value in data.items()
    }

    return json.dumps(
        prepared_data,
        separators=(",", ":")
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