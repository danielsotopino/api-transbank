from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from ..database import Base


class OneclickTransaction(Base):
    __tablename__ = 'oneclick_transactions'
    __table_args__ = {'schema': 'transbankoneclick'}
    
    id = Column(String(36), primary_key=True)
    username = Column(String(256), nullable=False, index=True)
    inscription_id = Column(String(36), ForeignKey('transbankoneclick.oneclick_inscriptions.id'), nullable=False)
    parent_buy_order = Column(String(255), nullable=False, unique=True, index=True)
    session_id = Column(String(255))
    transaction_date = Column(DateTime, nullable=False)
    accounting_date = Column(String(10))
    total_amount = Column(Integer, nullable=False)
    card_number_masked = Column(String(20))
    status = Column(String(20), nullable=False)  # approved, rejected, reversed, etc.
    raw_response = Column(Text)  # Store full Transbank response for audit
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    inscription = relationship("OneclickInscription", back_populates="transactions")
    details = relationship("OneclickTransactionDetail", back_populates="transaction", cascade="all, delete-orphan")


class OneclickTransactionDetail(Base):
    __tablename__ = 'oneclick_transaction_details'
    __table_args__ = {'schema': 'transbankoneclick'}
    
    id = Column(String(36), primary_key=True)
    transaction_id = Column(String(36), ForeignKey('transbankoneclick.oneclick_transactions.id'), nullable=False, index=True)
    commerce_code = Column(String(20), nullable=False)
    buy_order = Column(String(255), nullable=False)
    amount = Column(Integer, nullable=False)
    authorization_code = Column(String(20))
    payment_type_code = Column(String(5))
    response_code = Column(Integer, nullable=False)
    installments_number = Column(Integer, default=1)
    status = Column(String(20), nullable=False)  # approved, rejected, reversed, etc.
    balance = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationship
    transaction = relationship("OneclickTransaction", back_populates="details")