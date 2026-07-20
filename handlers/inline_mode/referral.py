import uuid

from aiogram import Router
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineQuery, InlineQueryResultsButton
from aiogram.utils.deep_linking import create_start_link
from aiogram.utils.payload import encode_payload

from database.service.lottery import LotteryService
from keyboards.inline import create_inline_ref_keyboard, inlinequery_lottery_keyboard
from utils.payload import create_payload, PayloadKey

router = Router()

@router.inline_query()
async def inline_query_handler(query: InlineQuery):
    text = query.query.strip()
    payload = create_payload({
        PayloadKey.REFERRER_ID: query.from_user.id
    })

    ref_link = await create_start_link(query.bot, payload)
    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"🔗 Поделиться реферальной ссылкой",
            description="Нажмите, чтобы отправить реферальную ссылку",
            input_message_content=InputTextMessageContent(
                message_text=(
                    "🚨 ОСТОРОЖНО! Я нашёл горячую лотерею 🔥\n\n"
                    "Тут можно попытать удачу и выиграть крутые призы 🎁\n\n"
                    "Я уже участвую — присоединяйся и ты 👇"
                )
            ),
            reply_markup=create_inline_ref_keyboard(ref_link)
        ),
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"Отправить: {text or 'Привет, как дела?'}",
            description="Нажмите, чтобы отправить сообщение",
            input_message_content=InputTextMessageContent(
                message_text="ЗХАЩВЫХЗАВЫХЗ!"
            )
        ),


    ]

    active_lotteries = await LotteryService.get_actives()
    inline_active_lotteries = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"🎉 Розыгрыш {lottery.prize}",
            description=f"Участников: {lottery.sold_tickets}/{lottery.total_tickets} | Lottio",
            input_message_content=InputTextMessageContent(
                message_text=(
                    f"🎉 <b>Розыгрыш: {lottery.prize}</b> | Lottio\n"
                    f"👥 Участников: {lottery.sold_tickets}/{lottery.total_tickets}\n\n"
                    f"🍀 Успей принять участие и получить шанс выиграть!"
                ),
            ),
            reply_markup=inlinequery_lottery_keyboard(
                link=await create_start_link(
                    query.bot,
                    f"lottery_{lottery.id}",
                    encode=True
                )
            )
        )
        for lottery in active_lotteries
    ]
    results.extend(inline_active_lotteries)

    await query.answer(
        results=results,
        cache_time=1,
        is_personal=True,
        button=InlineQueryResultsButton(
            text="🚀 Перейти в бота",
            start_parameter=encode_payload("start")
        )
    )