from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.service.user import UserService
from keyboards.inline import to_replenish_keyboard

router = Router()


@router.callback_query(F.data == "replenish")
async def replenish_handler(cbd: CallbackQuery):
    user = await UserService.get_user(cbd.message.chat.id)
    await cbd.message.answer(
        f"Ваш баланс: {user.balance}$\n\n",
        reply_markup=to_replenish_keyboard()
    )

