from datetime import datetime, timezone
from decimal import Decimal

from database.models import PaymentProvider, Transaction, PaymentStatus, User
from database.repo.transaction import TransactionRepository


class TransactionService:
    @staticmethod
    async def create_transaction(
        *,
        external_payment_id: str,
        user: User,
        amount: Decimal,
        provider: PaymentProvider,
        email: str | None = None,
        metadata: dict | None = None,
    ) -> Transaction:
        return await TransactionRepository.create(
            external_payment_id=external_payment_id,
            user=user,
            amount=amount,
            provider=provider,
            email=email,
            metadata=metadata,
        )

    @staticmethod
    async def complete_transaction(
        payment_id: str,
    ) -> Transaction | None:
        transaction = await TransactionRepository.get_pending_by_external_payment_id(
            payment_id
        )

        if transaction is None:
            return None

        transaction.status = PaymentStatus.COMPLETED
        transaction.completed_at = datetime.now(timezone.utc)

        await transaction.save()

        return transaction

    @staticmethod
    async def fail_transaction(
        external_payment_id: str,
    ) -> Transaction | None:
        transaction = await TransactionRepository.get_pending_by_external_payment_id(
            external_payment_id
        )

        if transaction is None:
            return None

        transaction.status = PaymentStatus.FAILED

        await transaction.save()

        return transaction

    @staticmethod
    async def cancel_transaction(
        external_payment_id: str,
    ) -> Transaction | None:
        transaction = await TransactionRepository.get_pending_by_external_payment_id(
            external_payment_id
        )

        if transaction is None:
            return None

        transaction.status = PaymentStatus.CANCELLED

        await transaction.save()

        return transaction

    @staticmethod
    async def get_transaction(
        external_payment_id: str,
    ) -> Transaction | None:
        return await TransactionRepository.get_by_external_payment_id_with_select_related(
            external_payment_id
        )