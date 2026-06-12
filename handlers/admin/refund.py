from aiogram import Bot
from aiogram import Router, F, types
from aiogram.exceptions import TelegramBadRequest

router = Router()


async def refund_stars_payment(
    bot: Bot,
    user_id: int,
    telegram_payment_charge_id: str
) -> bool:
    """
    Возвращает Telegram Stars пользователю.

    Уязвимости:
    - Переданный telegram_payment_charge_id должен строго браться
      из message.successful_payment.telegram_payment_charge_id
      (нельзя доверять клиенту или базе без проверки).
    """

    try:
        result = await bot.refund_star_payment(
            user_id=user_id,
            telegram_payment_charge_id=telegram_payment_charge_id
        )

        return result is True

    except TelegramBadRequest as e:
        # Частые причины:
        # - платеж уже возвращён
        # - неверный charge_id
        # - слишком старый платеж
        print(f"[REFUND ERROR] {e}")
        return False

    except Exception as e:
        print(f"[UNEXPECTED REFUND ERROR] {type(e).__name__}: {e}")
        return False

@router.message(F.text.startswith("/refund"))
async def refund_cmd(message: types.Message, bot: Bot):
    parts = message.text.split()

    if len(parts) != 2:
        await message.answer("Использование: /refund <charge_id>")
        return

    charge_id = parts[1]

    ok = await refund_stars_payment(
        bot=bot,
        user_id=message.from_user.id,
        telegram_payment_charge_id=charge_id
    )

    if ok:
        await message.answer("✅ Refund выполнен")
    else:
        await message.answer("❌ Refund не удался")