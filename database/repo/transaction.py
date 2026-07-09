from typing import Optional

from database.models import Transaction, PaymentStatus, User


class TransactionRepository:
    @staticmethod
    async def create(
        *,
        external_payment_id: str,
        user: User,
        amount,
        provider,
        email: str | None = None,
        metadata: dict | None = None,
    ) -> Transaction:
        return await Transaction.create(
            external_payment_id=external_payment_id,
            user=user,
            email=email,
            amount=amount,
            provider=provider,
            metadata=metadata or {},
        )

    @staticmethod
    async def get_by_id(transaction_id: int) -> Optional[Transaction]:
        return await Transaction.get_or_none(id=transaction_id)

    @staticmethod
    async def get_by_external_payment_id_with_select_related(
            external_payment_id: str,
    ) -> Transaction | None:
        return await (
            Transaction
            .get_or_none(external_payment_id=external_payment_id)
            .select_related("user")
        )

    @staticmethod
    async def get_pending_by_external_payment_id(
        external_payment_id: str,
    ) -> Optional[Transaction]:
        return await Transaction.get_or_none(
            external_payment_id=external_payment_id,
            status=PaymentStatus.PENDING,
        )

    @staticmethod
    async def get_last_user_transaction(
        telegram_id: int,
    ) -> Optional[Transaction]:
        return (
            await Transaction.filter(
                telegram_id=telegram_id
            )
            .order_by("-created_at")
            .first()
        )

    @staticmethod
    async def update(transaction: Transaction, **kwargs) -> Transaction:
        await transaction.update_from_dict(kwargs)
        await transaction.save()
        return transaction

    @staticmethod
    async def delete(transaction: Transaction) -> None:
        await transaction.delete()