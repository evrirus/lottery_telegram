from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.service.user import UserService
from keyboards.inline import to_replenish_keyboard, get_payment_method_keyboard

router = Router()


@router.callback_query(F.data == "replenish")
async def replenish_handler(cbd: CallbackQuery):
    user = await UserService.get_user(cbd.message.chat.id)
    await cbd.message.answer(
        f"Ваш баланс: {user.balance}р\n\n",
        reply_markup=to_replenish_keyboard()
    )

@router.callback_query(lambda c: c.data.startswith("replenish_"))
async def replenish__handler(cbd: CallbackQuery):
    amount = int(cbd.data.split("_")[1])
    await cbd.message.answer(
        "скоко?",
        reply_markup=get_payment_method_keyboard(
            user_id=cbd.message.chat.id,
            amount=amount
        )
    )
