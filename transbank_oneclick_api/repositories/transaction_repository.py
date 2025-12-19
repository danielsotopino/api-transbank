import structlog
from sqlalchemy.orm import Session, joinedload
from typing import Optional, List
from fastapi import Depends

from transbank_oneclick_api.models.oneclick_transaction import OneclickTransaction, OneclickTransactionDetail
from transbank_oneclick_api.repositories.base_repository import BaseRepository
from transbank_oneclick_api.database import get_db
from transbank_oneclick_api.domain.entities.transaction import TransactionEntity
from transbank_oneclick_api.domain.mappers.transaction_mapper import TransactionMapper

logger = structlog.get_logger(__name__)


class TransactionRepository(BaseRepository[OneclickTransaction]):
    """
    Repository for OneclickTransaction operations.

    Returns ORM models - Service layer converts to Pydantic.
    """

    def __init__(self, db: Session = Depends(get_db)):
        super().__init__(OneclickTransaction, db)
        self.db = db
        self.mapper = TransactionMapper()

    def create_with_details(
        self,
        transaction_data: dict,
        details_data: List[dict]
    ) -> OneclickTransaction:
        """
        Create transaction with details in a single operation.

        Args:
            transaction_data: Dictionary with transaction data
            details_data: List of dictionaries with transaction details

        Returns:
            OneclickTransaction: ORM model with details (NOT Pydantic)
        """
        logger.debug(
            "Creating transaction with details",
            transaction_id=transaction_data.get('id'),
            detail_count=len(details_data)
        )

        # Create transaction
        transaction = OneclickTransaction(**transaction_data)
        self.db.add(transaction)
        self.db.flush()  # Get transaction ID

        # Create details
        for detail_data in details_data:
            detail_data['transaction_id'] = transaction.id
            detail = OneclickTransactionDetail(**detail_data)
            self.db.add(detail)

        self.db.flush()
        logger.debug("Transaction and details created", transaction_id=transaction.id)

        return transaction

    def get_by_id_with_details(self, transaction_id: str) -> Optional[OneclickTransaction]:
        """
        Get transaction with details eagerly loaded.

        Args:
            transaction_id: Transaction ID

        Returns:
            OneclickTransaction | None: ORM model with details or None
        """
        logger.debug("Querying transaction with details", transaction_id=transaction_id)
        return self.db.query(OneclickTransaction).options(
            joinedload(OneclickTransaction.details)
        ).filter(OneclickTransaction.id == transaction_id).first()

    def get_by_username(
        self,
        username: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[OneclickTransaction]:
        """
        Get transactions by username with pagination.

        Args:
            username: Username to search
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[OneclickTransaction]: List of ORM models
        """
        logger.debug("Querying transactions by username", username=username)
        return self.db.query(OneclickTransaction).filter(
            OneclickTransaction.username == username
        ).order_by(OneclickTransaction.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_buy_order(self, buy_order: str) -> Optional[OneclickTransaction]:
        """
        Get transaction by buy_order.

        Args:
            buy_order: Buy order ID

        Returns:
            OneclickTransaction | None: ORM model or None
        """
        logger.debug("Querying transaction by buy_order", buy_order=buy_order)
        return self.db.query(OneclickTransaction).filter(
            OneclickTransaction.parent_buy_order == buy_order
        ).first()

    def find_by_buy_order_entity(self, buy_order: str) -> Optional[TransactionEntity]:
        """
        Get transaction by buy_order as Domain Entity.

        Args:
            buy_order: Buy order ID

        Returns:
            TransactionEntity | None: Domain entity or None
        """
        logger.debug("Querying transaction by buy_order (domain entity)", buy_order=buy_order)
        orm_model = self.get_by_buy_order(buy_order)
        return self.mapper.to_domain(orm_model) if orm_model else None

    def find_by_username_entity(
        self,
        username: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[TransactionEntity]:
        """
        Get transactions by username as Domain Entities.

        Args:
            username: Username to search
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[TransactionEntity]: List of domain entities
        """
        logger.debug("Querying transactions by username (domain entities)", username=username)
        orm_models = self.get_by_username(username, skip, limit)
        return [self.mapper.to_domain(orm) for orm in orm_models]

    def save_entity(self, transaction: TransactionEntity) -> TransactionEntity:
        """
        Save Domain Entity.

        Args:
            transaction: TransactionEntity to save

        Returns:
            TransactionEntity: Saved domain entity with details
        """
        logger.debug("Saving transaction entity", buy_order=transaction.buy_order)

        orm_model = self.mapper.to_orm(transaction)
        self.db.add(orm_model)
        self.db.flush()
        self.db.refresh(orm_model)

        logger.debug("Transaction entity saved", transaction_id=orm_model.id)
        return self.mapper.to_domain(orm_model)
