import random
from typing import Optional

from tortoise.transactions import in_transaction

from database.repo.lottery import LotteryRepository
from database.repo.ticket import TicketRepository


class WinnerService:

    @staticmethod
    async def pick_winner(lottery_id: int) -> Optional[int]:
        async with in_transaction():

            lottery = await LotteryRepository.get_for_update(lottery_id)

            if lottery.status != "active":
                return None

            # получаем (user_id, quantity)
            participants = await TicketRepository.get_user_quantities(lottery_id)

            if not participants:
                return None

            # weighted selection
            winner_id = WinnerService._weighted_choice(participants)

            lottery.status = "completed"
            lottery.winner_user_id = winner_id

            await LotteryRepository.save(lottery)

            return winner_id

    @staticmethod
    def _weighted_choice(participants: list[tuple[int, int]]) -> int:
        total_weight = sum(q for _, q in participants)

        if total_weight <= 0:
            raise ValueError("Invalid ticket quantities")

        r = random.randint(1, total_weight)

        current = 0
        for user_id, qty in participants:
            current += qty
            if r <= current:
                return user_id

        # fallback (теоретически не должен сработать)
        return participants[-1][0]