from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.orm import Session
from transbank_oneclick_api.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with generic CRUD operations.

    Responsibilities:
    - Only database operations (query, add, flush, delete)
    - Returns ORM models
    - NO commit/rollback (Service layer responsibility)
    - NO business logic
    """

    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def create(self, data: dict) -> ModelType:
        """
        Create a new record.

        Args:
            data: Dictionary with model data

        Returns:
            ModelType: ORM model instance (NOT Pydantic)
        """
        obj = self.model(**data)
        self.db.add(obj)
        self.db.flush()
        return obj

    def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        Get record by ID.

        Args:
            id: Record ID

        Returns:
            ModelType | None: ORM model or None if not found
        """
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """
        Get all records with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List[ModelType]: List of ORM models
        """
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def update(self, id: int, data: dict) -> Optional[ModelType]:
        """
        Update a record.

        Args:
            id: Record ID
            data: Dictionary with fields to update

        Returns:
            ModelType | None: Updated ORM model or None if not found
        """
        obj = self.get_by_id(id)
        if not obj:
            return None

        for field, value in data.items():
            if hasattr(obj, field):
                setattr(obj, field, value)

        self.db.flush()
        return obj

    def delete(self, id: int) -> bool:
        """
        Delete a record.

        Args:
            id: Record ID

        Returns:
            bool: True if deleted, False if not found
        """
        obj = self.get_by_id(id)
        if not obj:
            return False

        self.db.delete(obj)
        self.db.flush()
        return True
