from decimal import Decimal

from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.service.ticket import TicketService
from database.service.user import UserService
from keyboards.inline import to_replenish_keyboard, get_payment_method_keyboard
from service.lottery_logic import check_and_announce_winner
from utils.show.show_replenish import show_replenish

router = Router()


@router.callback_query(F.data == "replenish")
async def replenish_handler(callback: CallbackQuery):

    await show_replenish(
        user_id=callback.from_user.id,
        message=callback.message
    )

    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("replenish_"))
async def replenish__handler(cbd: CallbackQuery):
    amount = int(cbd.data.split("_")[1])
    await cbd.message.edit_text(
        "Выберите платёжное средство.",
        reply_markup=get_payment_method_keyboard(
            user_id=cbd.message.chat.id,
            amount=amount
        )
    )

@router.callback_query(lambda c: c.data.startswith("buy_tickets_"))
async def buy_tickets_handler(cbd: CallbackQuery):
    parts = cbd.data.split("_")
    qty = int(parts[2])
    lottery_id = int(parts[3])
    print(parts)

    success, reason = await TicketService.buy(lottery_id, cbd.from_user.id, qty)
    if success:
        await cbd.message.answer(f"Вы купили {qty} билетов!")
        await check_and_announce_winner(lottery_id, bot=cbd.bot)
        return

    await cbd.message.edit_text(reason)