from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class RecoveryAction(Base):
    """Typed, idempotent simulated gateway action - CLAUDE.md §15."""
    __tablename__ = "actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(
        Integer, ForeignKey("recovery_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_id = Column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    action_type = Column(String(50), nullable=False)   # silent_retry | smart_link | grace_period | human_escalation | suppress
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="INR")
    idempotency_key = Column(String(100), nullable=False, unique=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    policy_result = Column(JSON, nullable=False)        # full PolicyDecision dict

    case = relationship("RecoveryCase", back_populates="actions")
