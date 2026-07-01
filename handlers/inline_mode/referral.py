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
            title=f"Отправить: {text or 'Привет!'}",
            description="Нажмите, чтобы отправить сообщение",
            input_message_content=InputTextMessageContent(
                message_text=text or "Привет!"
            )
        ),
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title=f"Отправить: {text + "Я лох" or 'Привет, как дела?'}",
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