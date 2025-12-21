import structlog
from sqlalchemy.orm import Session
from typing import Optional
from fastapi import Depends

from transbank_oneclick_api.models.oneclick_inscription import OneclickInscription
from transbank_oneclick_api.repositories.base_repository import BaseRepository
from transbank_oneclick_api.database import get_db
from transbank_oneclick_api.domain.entities.inscription import InscriptionEntity
from transbank_oneclick_api.domain.mappers.inscription_mapper import InscriptionMapper

logger = structlog.get_logger(__name__)


class InscriptionRepository(BaseRepository[OneclickInscription]):
    """
    Repository for OneclickInscription operations.

    Returns ORM models - Service layer converts to Pydantic.
    """

    def __init__(self, db: Session = Depends(get_db)):
        super().__init__(OneclickInscription, db)
        self.db = db
        self.mapper = InscriptionMapper()

    def get_by_username(self, username: str) -> Optional[OneclickInscription]:
        """
        Get inscription by username.

        Args:
            username: Username to search

        Returns:
            OneclickInscription | None: ORM model or None
        """
        logger.debug("Querying inscription by username", username=username)
        return self.db.query(OneclickInscription).filter(
            OneclickInscription.username == username
        ).first()

    def get_by_tbk_user(self, tbk_user: str) -> Optional[OneclickInscription]:
        """
        Get inscription by Transbank user token.

        Args:
            tbk_user: Transbank user token

        Returns:
            OneclickInscription | None: ORM model or None
        """
        logger.debug("Querying inscription by tbk_user")
        return self.db.query(OneclickInscription).filter(
            OneclickInscription.tbk_user == tbk_user
        ).first()

    def get_active_by_username(self, username: str) -> Optional[OneclickInscription]:
        """
        Get active (COMPLETED) inscription by username.

        Args:
            username: Username to search

        Returns:
            OneclickInscription | None: ORM model or None
        """
        logger.debug("Querying active inscription", username=username)
        return self.db.query(OneclickInscription).filter(
            OneclickInscription.username == username,
            OneclickInscription.is_active
        ).first()

    def find_by_username_entity(self, username: str) -> Optional[InscriptionEntity]:
        """
        Get inscription by username as Domain Entity.

        Args:
            username: Username to search

        Returns:
            InscriptionEntity | None: Domain entity or None
        """
        logger.debug("Querying inscription by username (domain entity)", username=username)
        orm_model = self.get_by_username(username)
        return self.mapper.to_domain(orm_model) if orm_model else None

    def find_active_by_username_entity(self, username: str) -> Optional[InscriptionEntity]:
        """
        Get active inscription by username as Domain Entity.

        Args:
            username: Username to search

        Returns:
            InscriptionEntity | None: Domain entity or None
        """
        logger.debug("Querying active inscription (domain entity)", username=username)
        orm_model = self.get_active_by_username(username)
        return self.mapper.to_domain(orm_model) if orm_model else None

    def save_entity(self, inscription: InscriptionEntity) -> InscriptionEntity:
        """
        Save Domain Entity.

        Args:
            inscription: InscriptionEntity to save

        Returns:
            InscriptionEntity: Saved domain entity with updated ID
        """
        logger.debug("Saving inscription entity", username=inscription.username)

        if inscription.id:
            # Update existing
            orm_model = self.get_by_id(inscription.id)
            if not orm_model:
                raise ValueError(f"Inscription with id {inscription.id} not found")
            orm_model = self.mapper.update_orm_from_entity(orm_model, inscription)
        else:
            # Create new
            orm_model = self.mapper.to_orm(inscription)
            self.db.add(orm_model)

        self.db.flush()
        self.db.refresh(orm_model)

        logger.debug("Inscription entity saved", inscription_id=orm_model.id)
        return self.mapper.to_domain(orm_model)
