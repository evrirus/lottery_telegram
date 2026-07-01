# repositories/user_repo.py
from decimal import Decimal
from typing import Optional

from database.models import User


class UserRepository:

    @staticmethod
    async def create(telegram_id: int, referrer_id: Optional[int] = None) -> User:
        return await User.create(
            telegram_id=telegram_id,
            balance=Decimal("0.00"),
            referrer_id=referrer_id,
        )

    @staticmethod
    async def get_by_tg_id(telegram_id: int) -> User | None:
        return await User.get_or_none(telegram_id=telegram_id)

    @staticmethod
    async def get_for_update(telegram_id: int) -> User:
        return await User.select_for_update().get(telegram_id=telegram_id)

    @staticmethod
    async def save(user: User):
        await user.save()