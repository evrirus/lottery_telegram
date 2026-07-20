from typing import List

from tortoise.transactions import in_transaction

from database.models import LotteryStatus, Lottery
from database.repo.lottery import LotteryRepository


class LotteryService:

    @staticmethod
    async def create(prize, price, total, channel_id, photo_file_id = None):
        return await LotteryRepository.create(prize, price, total, channel_id, photo_file_id)

    @staticmethod
    async def get_actives() -> List[Lottery]:
        return await LotteryRepository.get_actives()

    @staticmethod
    async def get_lottery(
            lottery_id: int,
            status: LotteryStatus | None = None
    ):
        query = LotteryRepository.get_by_id(lottery_id)

        if status:
            query = query.filter(status=status)

        return await query.first()


    @staticmethod
    async def check_ticket_availability(lottery_id: int, quantity: int) -> bool:
        async with in_transaction():
            lottery = await LotteryRepository.get_for_update(lottery_id)

            if lottery.status != "active":
                return False

            available = lottery.total_tickets - lottery.sold_tickets

            return available >= quantity