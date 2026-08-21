from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    segment = Column(String(50), nullable=False)  # consumer, smb, enterprise
    ltv = Column(Numeric(12, 2), nullable=False)  # lifetime value in INR

    # Points to the customer's primary active subscription.
    # Nullable because during insert we create Customer first, then Subscription,
    # then update this FK. The use_alter=True handles the circular dependency with
    # Subscription.customer_id in the migration.
    subscription_id = Column(
        Integer,
        ForeignKey("subscriptions.id", use_alter=True, name="fk_customer_subscription_id"),
        nullable=True,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Primary subscription (via subscription_id FK)
    subscription = relationship(
        "Subscription",
        foreign_keys=[subscription_id],
        back_populates="customer",
        uselist=False,
    )
    # All subscriptions for this customer (via Subscription.customer_id)
    subscriptions = relationship(
        "Subscription",
        foreign_keys="Subscription.customer_id",
        back_populates="customer",
        overlaps="subscription",
    )
    payments = relationship("Payment", back_populates="customer")
    events = relationship("Event", back_populates="customer", order_by="Event.timestamp")
