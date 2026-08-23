from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


# Observable event types - the only simulator data the agent may ever see.
OBSERVABLE_EVENT_TYPES = frozenset({
    "invoice_viewed",
    "checkout_reopened",
    "payment_method_changed",
    "payment_failed",
    "subscription_changed",
    "support_message",
    "payment_delayed",
    "renewal_approaching",
})


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    # payload contains ONLY observable information - never latent state or outcome probabilities
    payload = Column(JSON, nullable=False, default=dict)

    customer = relationship("Customer", back_populates="events")
