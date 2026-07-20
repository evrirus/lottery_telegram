from aiogram import Router, types, F
from aiogram.filters import Command

from database.models import LotteryStatus
from database.service.lottery import LotteryService
from database.service.ticket import TicketService
from keyboards.inline import my_tickets_keyboard, cancel_button
from utils.show_lottery import show_lottery

router = Router()

async def my_tickets_logic(
        *,
        target: types.Message | types.CallbackQuery,
        text: str,
        else_text: str,
        user_id: int,
        status: LotteryStatus = None
):
    tickets = await TicketService.get_user_tickets(target.from_user.id, status=status)
    if not tickets:
        keyboard = cancel_button("start")
        text = else_text
    else:
        keyboard = my_tickets_keyboard(tickets, user_id)

    message = target.message if isinstance(target, types.CallbackQuery) else target

    if isinstance(target, types.Message):
        await target.answer(text, reply_markup=keyboard)
        return

    await message.edit_text(text, reply_markup=keyboard)

@router.message(Command("my_tickets"))
async def my_tickets_handler(message):
    text = "Ваши активные билеты."
    else_text = "Участвуйте в лотереях, чтобы просматривать активные билеты!"
    await my_tickets_logic(
        target=message,
        text=text,
        else_text=else_text,
        status=LotteryStatus.ACTIVE,
        user_id=message.from_user.id
    )

@router.callback_query(F.data == "my_tickets")
async def my_tickets_callback(callback: types.CallbackQuery):
    text = "Ваши активные билеты."
    else_text = "Участвуйте в лотереях, чтобы просматривать активные билеты!"
    await my_tickets_logic(
        target=callback,
        text=text,
        else_text=else_text,
        status=LotteryStatus.ACTIVE,
        user_id=callback.from_user.id
    )


@router.callback_query(F.data == "my_history")
async def my_history_callback(callback: types.CallbackQuery):
    text = "История ваших лотерей"
    else_text = "Участвуйте в лотереях, чтобы ознакомиться с историей!"
    await my_tickets_logic(
        target=callback,
        text=text,
        else_text=else_text,
        user_id=callback.from_user.id
    )

@router.message(Command("my_history"))
async def my_history_handler(message: types.Message):
    text = "История ваших лотерей"
    else_text = "Участвуйте в лотереях, чтобы ознакомиться с историей!"
    await my_tickets_logic(
        target=message,
        text=text,
        else_text=else_text,
        user_id=message.from_user.id
    )


@router.callback_query(lambda c: c.data.startswith("lottery_"))
async def check_lottery_by_id_handler(callback: types.CallbackQuery):
    lottery_id = int(callback.data.split("_")[1])

    await show_lottery(
        bot=callback.bot,
        user_id=callback.from_user.id,
        message=callback.message,
        lottery_id=lottery_id
    )