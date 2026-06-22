import random
from tortoise.transactions import in_transaction

from database.repo.lottery import LotteryRepository
from database.repo.ticket import TicketRepository


class WinnerService:

    @staticmethod
    async def pick_winner(lottery_id: int) -> int | None:
        async with in_transaction():

            # 1. блокируем лотерею (защита от race condition)
            lottery = await LotteryRepository.get_for_update(lottery_id)

            if lottery.status != "active":
                return None

            # 2. получаем всех участников
            user_ids = await TicketRepository.get_all_user_ids(lottery_id)

            if not user_ids:
                return None

            # 3. выбираем победителя (O(n), но безопасно)
            winner_id = random.choice(user_ids)

            # 4. обновляем лотерею
            lottery.status = "completed"
            lottery.winner_user_id = winner_id

            await LotteryRepository.save(lottery)

            return winner_id