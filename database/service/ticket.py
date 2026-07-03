from typing import Tuple, Optional

from tortoise.transactions import in_transaction, F

from database.models import Ticket, Lottery, User, LotteryStatus
from database.repo.ticket import TicketRepository


class TicketService:

    @staticmethod
    async def buy(lottery_id: int, user_id: int, quantity: int) -> Tuple[bool, str]:
        async with in_transaction():

            lottery = await Lottery.filter(id=lottery_id).select_for_update().first()
            if not lottery:
                return False, "Лотерея не найдена"

            remaining = lottery.total_tickets - lottery.sold_tickets
            if quantity <= 0 or quantity > remaining:
                return False, "Недостаточно билетов"

            total_price = lottery.ticket_price * quantity

            # ✔ атомарный withdraw (без сервиса)
            updated = await User.filter(
                id=user_id,
                balance__gte=total_price
            ).update(
                balance=F("balance") - total_price
            )

            if not updated:
                return False, "Недостаточно средств"

            # ✔ обновление билетов
            await Lottery.filter(id=lottery_id).update(
                sold_tickets=F("sold_tickets") + quantity
            )

            # ✔ UPSERT БЕЗ update_or_create (ВАЖНО)
            updated = await Ticket.filter(
                lottery_id=lottery_id,
                user_id=user_id
            ).update(
                quantity=F("quantity") + quantity
            )

            if not updated:
                await Ticket.create(
                    lottery_id=lottery_id,
                    user_id=user_id,
                    quantity=quantity
                )

            return True, "ok"

    @staticmethod
    async def get_user_tickets(telegram_id: int, status: Optional[LotteryStatus] = None) -> list[Ticket]:
        return await TicketRepository.get_user_tickets(telegram_id, status=status)

