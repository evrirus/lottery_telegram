from aiogram import Bot, types
from aiogram.utils.deep_linking import create_start_link

from database.models import LotteryStatus
from database.service.lottery import LotteryService
from keyboards.inline import cancel_button
from utils.payload import create_payload, PayloadKey


async def show_lottery(
    bot: Bot,
    user_id: int,
    message: types.Message,
    lottery_id: int
):
    print("SEARCH ID:", lottery_id)

    lottery = await LotteryService.get_lottery(
        lottery_id=lottery_id
    )

    print("RESULT:", lottery)
    text = (
        f"🎁 <b>Лотерея #{lottery.id}</b>\n\n"
        f"🏆 Приз: {lottery.prize}\n"
        f"💰 Цена билета: {lottery.ticket_price_display} ⭐️\n"
        f"📊 Продано: {lottery.sold_tickets} из {lottery.total_tickets}\n\n"
    )

    if lottery.status == LotteryStatus.COMPLETED and lottery.winner_user_id == user_id:
        text += "👑 <b>Победитель: ВЫ</b> 🥳🥳🥳"

    elif lottery.status == LotteryStatus.COMPLETED:
        winner = await bot.get_chat(lottery.winner_user_id)
        url = f'<a href="tg://user?id={winner.id}">{winner.full_name}</a>'
        text += f"<b>Победитель: {url}</b>"

    else:
        bot_info = await bot.get_me()
        payload = create_payload({
            PayloadKey.LOTTERY_ID: lottery_id,
        })
        link = await create_start_link(
            bot, payload
        )
        text += f'<b>Лотерея активна, <a href="{link}">участвуйте!</a></b>'

    if isinstance(message, types.Message):
        return await message.answer(
            text,
            reply_markup=cancel_button("start")
        )

    await message.message.answer(
        text,
        reply_markup=cancel_button("start")
    )
