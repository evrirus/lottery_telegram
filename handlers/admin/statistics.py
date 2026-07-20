from aiogram import Router, types
from aiogram.filters import Command

from database.service.user import UserService

router = Router()

@router.message(Command("users"))
async def get_users(message: types.Message):
    users = await UserService.get_all_users()

    if not users:
        return await message.answer("👥 Пользователей пока нет")

    text = "👥 <b>Пользователи:</b>\n\n"

    for user in users:
        text += (
            f"<blockquote>🆔 <code>{user.telegram_id}</code>\n"
            f"💰 Баланс: {user.balance_display}\n"
            f"📅 Регистрация: {user.register_at:%d.%m.%Y %H:%M}</blockquote>\n"
        )

    await message.answer(text)

