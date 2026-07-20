# repositories/lottery_repo.py
from typing import Optional

from database.models import Lottery, LotteryStatus


class LotteryRepository:

    @staticmethod
    async def create(prize, price, total, channel_id, photo_file_id = None):
        return await Lottery.create(
            prize=prize,
            ticket_price=price,
            total_tickets=total,
            channel_id=channel_id,
            photo_file_id=photo_file_id
        )

    @staticmethod
    async def get_actives(limit: int | None = None):
        query = Lottery.filter(
            status=LotteryStatus.ACTIVE
        ).order_by("-id")

        if limit:
            query = query.limit(limit)

        return await query

    @staticmethod
    def get_by_id(lottery_id: int):
        return Lottery.filter(id=lottery_id)

    @staticmethod
    async def get_for_update(lottery_id: int):
        return await Lottery.select_for_update().get(id=lottery_id)

    @staticmethod
    async def save(lottery: Lottery):
        await lottery.save()

