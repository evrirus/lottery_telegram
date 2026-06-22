# repositories/lottery_repo.py
from database.models import Lottery


class LotteryRepository:

    @staticmethod
    async def create(prize, price, total, channel_id):
        return await Lottery.create(
            prize=prize,
            ticket_price=price,
            total_tickets=total,
            channel_id=channel_id
        )

    @staticmethod
    async def get_actives():
        return await Lottery.filter(status="active").order_by("-id").first()

    @staticmethod
    async def get_by_id(lottery_id: int):
        return await Lottery.get_or_none(id=lottery_id)

    @staticmethod
    async def get_for_update(lottery_id: int):
        return await Lottery.select_for_update().get(id=lottery_id)

    @staticmethod
    async def save(lottery: Lottery):
        await lottery.save()

