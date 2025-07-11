from fastapi import Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.transbank_service import TransbankService


def get_transbank_service() -> TransbankService:
    return TransbankService()


def get_database_session() -> Session:
    return Depends(get_db)