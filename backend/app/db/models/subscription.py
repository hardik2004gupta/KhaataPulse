from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    plan = Column(String(100), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)   # INR, exact representation
    currency = Column(String(3), nullable=False, default="INR")
    renewal_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(50), nullable=False)       # active, cancelled, paused

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    customer = relationship(
        "Customer",
        foreign_keys=[customer_id],
        back_populates="subscriptions",
    )
    payments = relationship("Payment", back_populates="subscription")
