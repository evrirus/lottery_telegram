# repositories/ticket_repo.py
from database.models import Lottery, User, Ticket


class TicketRepository:

    @staticmethod
    async def create(lottery: Lottery, user: User):
        return await Ticket.create(
            lottery=lottery,
            user=user
        )

    @staticmethod
    async def count_by_lottery(lottery_id: int) -> int:
        return await Ticket.filter(lottery_id=lottery_id).count()

    @staticmethod
    async def get_all_user_ids(lottery_id: int) -> list[int]:
        tickets = await Ticket.filter(lottery_id=lottery_id).values_list("user_id", flat=True)
        return list(tickets)