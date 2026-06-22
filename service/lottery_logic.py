from aiogram import Bot

from database.service.lottery import LotteryService
from database.service.winner import WinnerService


async def check_and_announce_winner(lottery_id: int, bot: Bot = None):
    lottery = await LotteryService.get_lottery(lottery_id)

    if lottery.sold_tickets >= lottery.total_tickets:
        # Билеты кончились! Выбираем победителя
        winner_id = await WinnerService.pick_winner(lottery_id)

        if winner_id:
            winner = await bot.get_chat(winner_id)
            print(winner)
            winner_username = f"@{winner.username}"  # В реальном коде лучше получить username через bot.get_chat(winner_id)

            announcement_text = (
                f"🎉 <b>ЛОТЕРЕЯ ЗАВЕРШЕНА!</b> 🎉\n\n"
                f"Приз: {lottery.prize}\n"
                f"Всего продано билетов: {lottery.total_tickets}\n\n"
                f"🏆 <b>ПОБЕДИТЕЛЬ:</b> {winner_username} 🏆\n\n"
                f"Поздравляем! Свяжитесь с администратором для получения приза."
            )

            try:
                # Отправляем пост в указанный канал
                await bot.send_message(
                    chat_id=lottery.channel_id,
                    text=announcement_text
                )
                # Опционально: уведомить победителя в ЛС
                await bot.send_message(winner_id, "🎉 Поздравляем! Вы выиграли в лотерее! Свяжитесь с <a href=\"tg://user?id=899827113\">админом</a>.")
            except Exception as e:
                print(f"Ошибка отправки в канал: {e}")