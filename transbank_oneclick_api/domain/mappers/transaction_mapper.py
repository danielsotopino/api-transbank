from typing import List
import uuid
from transbank_oneclick_api.domain.entities.transaction import (
    TransactionEntity,
    TransactionDetail,
    Amount,
    TransactionStatus,
    PaymentType
)
from transbank_oneclick_api.models.oneclick_transaction import (
    OneclickTransaction,
    OneclickTransactionDetail
)


class TransactionMapper:
    """
    Mapper between TransactionEntity (domain) and OneclickTransaction (ORM).

    Handles transaction with nested details.
    """

    @staticmethod
    def to_domain(orm_model: OneclickTransaction) -> TransactionEntity:
        """
        Convert ORM model to domain entity.

        Args:
            orm_model: OneclickTransaction ORM model with details loaded

        Returns:
            TransactionEntity: Domain entity with details
        """
        # Convert details
        details = [
            TransactionMapper._detail_to_domain(detail_orm)
            for detail_orm in orm_model.details
        ]

        # Map card_number_masked to card_number
        card_number = getattr(orm_model, 'card_number_masked', None) or getattr(orm_model, 'card_number', None)

        # Map parent_buy_order to buy_order
        buy_order = getattr(orm_model, 'parent_buy_order', None) or getattr(orm_model, 'buy_order', None)

        return TransactionEntity(
            id=orm_model.id,
            username=orm_model.username,
            buy_order=buy_order,
            card_number=card_number,
            accounting_date=orm_model.accounting_date,
            transaction_date=orm_model.transaction_date,
            created_at=orm_model.created_at,
            details=details
        )

    @staticmethod
    def _detail_to_domain(
        detail_orm: OneclickTransactionDetail
    ) -> TransactionDetail:
        """Convert ORM detail to domain detail."""
        return TransactionDetail(
            id=detail_orm.id,
            commerce_code=detail_orm.commerce_code,
            buy_order=detail_orm.buy_order,
            amount=Amount(value=detail_orm.amount),
            status=TransactionStatus(detail_orm.status),
            authorization_code=detail_orm.authorization_code,
            payment_type_code=(
                PaymentType(detail_orm.payment_type_code)
                if detail_orm.payment_type_code else None
            ),
            response_code=detail_orm.response_code,
            installments_number=detail_orm.installments_number
        )

    @staticmethod
    def to_orm(entity: TransactionEntity) -> OneclickTransaction:
        """
        Convert domain entity to ORM model.

        Args:
            entity: TransactionEntity domain entity

        Returns:
            OneclickTransaction: ORM model with details
        """

        # Generate UUID if id is not provided
        transaction_id = entity.id if entity.id else str(uuid.uuid4())
        
        # Calculate total amount from details
        total_amount = sum(detail.amount.value for detail in entity.details)

        orm_model = OneclickTransaction(
            id=transaction_id,
            username=entity.username,
            accounting_date=entity.accounting_date,
            transaction_date=entity.transaction_date,
            created_at=entity.created_at,
            total_amount=total_amount,
            status=entity.details[0].status.value if entity.details else TransactionStatus.AUTHORIZED.value
        )

        # Map buy_order to parent_buy_order if field exists
        if hasattr(OneclickTransaction, 'parent_buy_order'):
            orm_model.parent_buy_order = entity.buy_order
        elif hasattr(OneclickTransaction, 'buy_order'):
            orm_model.buy_order = entity.buy_order

        # Map card_number to card_number_masked if field exists
        if entity.card_number:
            if hasattr(OneclickTransaction, 'card_number_masked'):
                orm_model.card_number_masked = entity.card_number
            elif hasattr(OneclickTransaction, 'card_number'):
                orm_model.card_number = entity.card_number

        # Convert details
        orm_model.details = [
            TransactionMapper._detail_to_orm(detail, transaction_id)
            for detail in entity.details
        ]

        return orm_model

    @staticmethod
    def _detail_to_orm(
        detail: TransactionDetail,
        transaction_id: str
    ) -> OneclickTransactionDetail:
        """Convert domain detail to ORM detail."""
        return OneclickTransactionDetail(
            id=detail.id if detail.id else str(uuid.uuid4()),
            transaction_id=transaction_id,
            commerce_code=detail.commerce_code,
            buy_order=detail.buy_order,
            amount=detail.amount.value,
            status=detail.status.value,
            authorization_code=detail.authorization_code,
            payment_type_code=(
                detail.payment_type_code.value
                if detail.payment_type_code else None
            ),
            response_code=detail.response_code,
            installments_number=detail.installments_number
        )
