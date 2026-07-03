# repositories/ticket_repo.py
from typing import Optional

from database.models import Lottery, User, Ticket, LotteryStatus


class TicketRepository:

    @staticmethod
    async def create(lottery: Lottery, user: User, quantity: int):
        return await Ticket.create(
            lottery=lottery,
            user=user,
            quantity=quantity
        )

    @staticmethod
    async def count_by_lottery(lottery_id: int) -> int:
        return await Ticket.filter(lottery_id=lottery_id).count()

    @staticmethod
    async def get_all_user_ids(lottery_id: int) -> list[int]:
        tickets = await Ticket.filter(
            lottery_id=lottery_id
        ).values_list("user__telegram_id", flat=True)

        return list(tickets)

    @staticmethod
    async def get_user_quantities(lottery_id: int) -> list[tuple[int, int]]:
        rows = await Ticket.filter(
            lottery_id=lottery_id
        ).values_list("user__telegram_id", "quantity")

        return list(rows)

    @staticmethod
    async def get_user_tickets(telegram_id: int, status: Optional[LotteryStatus] = None) -> list[Ticket]:
        query = Ticket.filter(user__telegram_id=telegram_id)

        if status is not None:
            query = query.filter(lottery__status=status)

        return await query.select_related("lottery", "user")

    @staticmethod
    async def save(ticket: Ticket) -> Ticket:
        updated = await Ticket.filter(
            id=ticket.id,
            quantity=ticket.quantity  # optimistic lock (если есть контроль состояния)
        ).update(
            quantity=ticket.quantity
        )

        if not updated:
            raise Exception("Concurrent update detected")

        return ticket

