from typing import Optional
from transbank_oneclick_api.domain.entities.inscription import (
    InscriptionEntity,
    InscriptionStatus,
    CardDetails
)
from transbank_oneclick_api.models.oneclick_inscription import OneclickInscription


class InscriptionMapper:
    """
    Mapper between InscriptionEntity (domain) and OneclickInscription (ORM).

    Responsibilities:
    - Convert Domain Entity → ORM Model
    - Convert ORM Model → Domain Entity
    - Handle CardDetails value object
    """

    @staticmethod
    def to_domain(orm_model: OneclickInscription) -> InscriptionEntity:
        """
        Convert ORM model to domain entity.

        Args:
            orm_model: OneclickInscription ORM model

        Returns:
            InscriptionEntity: Domain entity
        """
        # Convert CardDetails if present
        card_details = None
        if hasattr(orm_model, 'card_type') and hasattr(orm_model, 'card_number'):
            if orm_model.card_type and orm_model.card_number:
                card_details = CardDetails(
                    card_type=orm_model.card_type,
                    card_number=orm_model.card_number
                )
        elif hasattr(orm_model, 'card_number_masked') and orm_model.card_number_masked:
            # Fallback for old schema with card_number_masked
            if hasattr(orm_model, 'card_type') and orm_model.card_type:
                card_details = CardDetails(
                    card_type=orm_model.card_type,
                    card_number=orm_model.card_number_masked
                )

        # Handle status field (new schema) or is_active (old schema)
        if hasattr(orm_model, 'status'):
            status = InscriptionStatus(orm_model.status)
        elif hasattr(orm_model, 'is_active'):
            # Map is_active to status for backward compatibility
            status = InscriptionStatus.COMPLETED if orm_model.is_active else InscriptionStatus.PENDING
        else:
            status = InscriptionStatus.PENDING

        # Handle url_webpay field
        url_webpay = getattr(orm_model, 'url_webpay', '')

        return InscriptionEntity(
            id=orm_model.id,
            username=orm_model.username,
            email=orm_model.email,
            tbk_user=orm_model.tbk_user,
            url_webpay=url_webpay,
            status=status,
            card_details=card_details,
            authorization_code=orm_model.authorization_code,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at
        )

    @staticmethod
    def to_orm(entity: InscriptionEntity) -> OneclickInscription:
        """
        Convert domain entity to ORM model.

        Args:
            entity: InscriptionEntity domain entity

        Returns:
            OneclickInscription: ORM model
        """
        orm_model = OneclickInscription(
            id=entity.id,
            username=entity.username,
            email=entity.email,
            tbk_user=entity.tbk_user,
            authorization_code=entity.authorization_code,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

        # Set url_webpay if field exists
        if hasattr(OneclickInscription, 'url_webpay'):
            orm_model.url_webpay = entity.url_webpay

        # Set status if field exists, otherwise use is_active
        if hasattr(OneclickInscription, 'status'):
            orm_model.status = entity.status.value
        elif hasattr(OneclickInscription, 'is_active'):
            orm_model.is_active = (entity.status == InscriptionStatus.COMPLETED)

        # Map CardDetails if present
        if entity.card_details:
            orm_model.card_type = entity.card_details.card_type
            # Try card_number first, then card_number_masked
            if hasattr(OneclickInscription, 'card_number'):
                orm_model.card_number = entity.card_details.card_number
            elif hasattr(OneclickInscription, 'card_number_masked'):
                orm_model.card_number_masked = entity.card_details.card_number

        return orm_model

    @staticmethod
    def update_orm_from_entity(
        orm_model: OneclickInscription,
        entity: InscriptionEntity
    ) -> OneclickInscription:
        """
        Update existing ORM model with entity data.

        Useful for updates without creating new instances.

        Args:
            orm_model: Existing ORM model to update
            entity: Domain entity with new data

        Returns:
            OneclickInscription: Updated ORM model
        """
        orm_model.username = entity.username
        orm_model.email = entity.email
        orm_model.tbk_user = entity.tbk_user
        orm_model.authorization_code = entity.authorization_code
        orm_model.updated_at = entity.updated_at

        # Set url_webpay if field exists
        if hasattr(OneclickInscription, 'url_webpay'):
            orm_model.url_webpay = entity.url_webpay

        # Set status if field exists, otherwise use is_active
        if hasattr(OneclickInscription, 'status'):
            orm_model.status = entity.status.value
        elif hasattr(OneclickInscription, 'is_active'):
            orm_model.is_active = (entity.status == InscriptionStatus.COMPLETED)

        # Map CardDetails if present
        if entity.card_details:
            orm_model.card_type = entity.card_details.card_type
            # Try card_number first, then card_number_masked
            if hasattr(OneclickInscription, 'card_number'):
                orm_model.card_number = entity.card_details.card_number
            elif hasattr(OneclickInscription, 'card_number_masked'):
                orm_model.card_number_masked = entity.card_details.card_number

        return orm_model
