from decimal import Decimal

from aiogram import types, Bot

from database.service.user import UserService
from keyboards.inline import to_replenish_keyboard


async def show_replenish(
    user_id: int,
    message: types.Message
):
    user = await UserService.get_user(user_id)

    balance = user.balance.quantize(Decimal("1"))

    await message.answer(
        f"Ваш баланс: {balance}₽\n\n",
        reply_markup=to_replenish_keyboard()
    )