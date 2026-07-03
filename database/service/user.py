# services/user_service.py
from decimal import Decimal
from typing import Optional

from tortoise.transactions import in_transaction

from database.models import User
from database.repo.user import UserRepository


class UserService:

    @staticmethod
    async def register(telegram_id: int, referrer_id: Optional[int] = None) -> tuple[User, bool]:

        user = await UserRepository.get_by_tg_id(telegram_id)
        if user:
            return user, False

        valid_referrer_id = None

        if referrer_id:
            referrer = await UserRepository.get_by_tg_id(referrer_id)

            if referrer and referrer.telegram_id != telegram_id:
                valid_referrer_id = referrer.telegram_id

        return await UserRepository.create(
            telegram_id,
            referrer_id=valid_referrer_id
        ), True

    @staticmethod
    async def add_balance(telegram_id: int, amount: Decimal):
        async with in_transaction():
            user = await UserRepository.get_for_update(telegram_id)
            amount = Decimal(str(amount))  # ключевой фикс
            user.balance += amount
            await UserRepository.save(user)
            return user.balance

    @staticmethod
    async def withdraw(user_id: int, amount: Decimal) -> bool:
        return await UserRepository.withdraw(user_id, amount)

    @staticmethod
    async def get_user(telegram_id: int):
        return await UserRepository.get_by_tg_id(telegram_id)