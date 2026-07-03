from aiogram import Router, types, F
from aiogram.filters import Command

from database.models import LotteryStatus
from database.service.lottery import LotteryService
from database.service.ticket import TicketService
from keyboards.inline import my_tickets_keyboard, cancel_button

router = Router()

async def my_tickets_logic(*, target: types.Message | types.CallbackQuery, text: str, status: LotteryStatus = None):
    tickets = await TicketService.get_user_tickets(target.from_user.id, status=status)
    keyboard = my_tickets_keyboard(tickets)

    message = target.message if isinstance(target, types.CallbackQuery) else target

    if isinstance(target, types.Message):
        await target.answer(text, reply_markup=keyboard)
        return

    await message.edit_text(text, reply_markup=keyboard)

@router.message(Command("my_tickets"))
async def my_tickets_handler(message):
    text = "Ваши активные билеты."
    await my_tickets_logic(target=message, text=text, status=LotteryStatus.ACTIVE)

@router.callback_query(F.data == "my_tickets")
async def my_tickets_callback(callback: types.CallbackQuery):
    text = "Ваши активные билеты."
    await my_tickets_logic(target=callback, text=text, status=LotteryStatus.ACTIVE)


@router.callback_query(F.data == "my_history")
async def my_history_callback(callback: types.CallbackQuery):
    text = ""
    await my_tickets_logic(target=callback, text=text)

@router.message(Command("my_history"))
async def my_history_handler(message: types.Message):
    text = ""
    await my_tickets_logic(target=message, text=text)


@router.callback_query(lambda c: c.data.startswith("lottery_"))
async def check_lottery_by_id_handler(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    lottery_id = int(parts[1]) if parts[1] and parts[1].isdigit() else None

    lottery = await LotteryService.get_lottery(lottery_id=lottery_id)
    text = (
        f"🎁 <b>Лотерея #{lottery.id}</b>\n\n"
        f"🏆 Приз: {lottery.prize}\n"
        f"💰 Цена билета: {lottery.ticket_price_display} ⭐️\n"
        f"📊 Продано: {lottery.sold_tickets} из {lottery.total_tickets}\n\n"
    )
    await callback.message.edit_text(text, reply_markup=cancel_button("start"))