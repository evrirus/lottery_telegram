from typing import Tuple

from tortoise.transactions import in_transaction

from database.repo.lottery import LotteryRepository
from database.repo.ticket import TicketRepository
from database.service.user import UserService


class TicketService:

    @staticmethod
    async def buy(lottery_id: int, user_id: int, quantity: int) -> Tuple[bool, str]:
        async with in_transaction():

            lottery = await LotteryRepository.get_for_update(lottery_id)
            if not lottery:
                return False, "Лотерея не найдена"

            user = await UserService.get_user(user_id)
            total_price = lottery.ticket_price * quantity
            if user.balance < total_price:
                return False, "Недостаточно средств"

            if lottery.sold_tickets + quantity > lottery.total_tickets:
                return False, "В продаже отсутствует достаточное количество билетов"

            await UserService.withdraw(user_id, total_price)
            for _ in range(quantity):
                await TicketRepository.create(lottery, user)

            lottery.sold_tickets += quantity

            await LotteryRepository.save(lottery)

            return True, "ok"