from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import settings
from .models.base import Base

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()