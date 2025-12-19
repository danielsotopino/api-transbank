from fastapi import Depends
from sqlalchemy.orm import Session
from transbank_oneclick_api.database import get_db
from transbank_oneclick_api.services.transbank_service import TransbankService


def get_transbank_service(db: Session = Depends(get_db)) -> TransbankService:
    return TransbankService(db=db)


def get_database_session() -> Session:
    return get_db()