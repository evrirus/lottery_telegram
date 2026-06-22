from aiogram import Router, F
from aiogram.types import CallbackQuery

from database.service.lottery import LotteryService
from database.service.ticket import TicketService
from database.service.user import UserService
from database.service.winner import WinnerService
from keyboards.inline import to_replenish_keyboard, get_payment_method_keyboard
from service.lottery_logic import check_and_announce_winner

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

    await cbd.message.answer(reason)