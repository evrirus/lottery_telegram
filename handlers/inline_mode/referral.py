import uuid

from aiogram import Router
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent, InlineQuery

router = Router()

@router.inline_query()
async def inline_query_handler(query: InlineQuery):
    text = query.query.strip()

    results = [
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"Выслать приглашение",
            description="Нажмите, чтобы отправить реферальную ссылку",
            input_message_content=InputTextMessageContent(
                message_text=f'Приглашаю тебя в бот лотерея: <a href="tg://resolve?domain=gotgm_bot&start={query.from_user.id}">Переходи по ссылке</a>'
            )
        ),
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"Отправить: {text or 'Привет, как дела?'}",
            description="Нажмите, чтобы отправить сообщение",
            input_message_content=InputTextMessageContent(
                message_text="ЗХАЩВЫХЗАВЫХЗ!"
            )
        )
    ]

    await query.answer(
        results=results,
        cache_time=1,
        is_personal=True
    )