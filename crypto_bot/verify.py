import hashlib
import hmac

from flask import request


def verify_crypto_pay_signature(token: str, request: request) -> bool:
    # 1. секрет = SHA256(token)
    secret = hashlib.sha256(token.encode()).digest()

    # 2. сырой body (ВАЖНО: не request.json)
    body = request.get_data()  # bytes

    # 3. signature из header
    signature = request.headers.get("crypto-pay-api-signature")

    if not signature:
        return False

    # 4. HMAC-SHA256 от body
    computed = hmac.new(
        secret,
        body,
        hashlib.sha256
    ).hexdigest()

    # 5. безопасное сравнение
    return hmac.compare_digest(computed, signature)