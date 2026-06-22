from tortoise.transactions import in_transaction

from database.repo.lottery import LotteryRepository
from database.repo.ticket import TicketRepository


class TicketService:

    @staticmethod
    async def buy(lottery_id: int, user, quantity: int) -> bool:
        async with in_transaction():
            lottery = await LotteryRepository.get_for_update(lottery_id)

            if not lottery:
                return False

            if lottery.sold_tickets + quantity > lottery.total_tickets:
                return False

            for _ in range(quantity):
                await TicketRepository.create(lottery, user)

            lottery.sold_tickets += quantity
            await LotteryRepository.save(lottery)

            return True