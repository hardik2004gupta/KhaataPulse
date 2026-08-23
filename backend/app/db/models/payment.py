from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False, index=True)
    amount = Column(Numeric(12, 2), nullable=False)
    status = Column(String(50), nullable=False)        # successful, failed, pending
    failure_code = Column(String(100), nullable=True)  # NULL on success
    payment_method = Column(String(50), nullable=False) # upi, card, net_banking, wallet
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    customer = relationship("Customer", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")
