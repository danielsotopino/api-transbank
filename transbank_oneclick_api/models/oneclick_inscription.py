from sqlalchemy import Column, String, DateTime, Boolean, Text, func
from sqlalchemy.orm import relationship
from ..database import Base


class OneclickInscription(Base):
    __tablename__ = 'oneclick_inscriptions'
    __table_args__ = {'schema': 'transbankoneclick'}
    
    id = Column(String(36), primary_key=True)
    username = Column(String(256), nullable=False, index=True)
    email = Column(String(254), nullable=True)
    tbk_user = Column(Text, nullable=False)  # Encrypted
    card_type = Column(String(50))
    card_number_masked = Column(String(20))  # Only last 4 digits
    authorization_code = Column(String(20))
    inscription_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationship with transactions
    transactions = relationship("OneclickTransaction", back_populates="inscription")