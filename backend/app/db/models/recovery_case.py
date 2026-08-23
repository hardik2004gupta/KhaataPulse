from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class RecoveryCase(Base):
    """One recovery case per customer risk detection event."""
    __tablename__ = "recovery_cases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(
        Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    risk_score = Column(Numeric(6, 4), nullable=False)
    risk_level = Column(String(10), nullable=False)       # LOW | MEDIUM | HIGH
    diagnosis = Column(String(50), nullable=True)          # cause enum
    diagnosis_confidence = Column(Numeric(5, 4), nullable=True)
    proposed_action = Column(String(50), nullable=True)
    selected_action = Column(String(50), nullable=True)
    policy_status = Column(String(20), nullable=True)     # APPROVED | BLOCKED | ESCALATED
    outcome_status = Column(String(20), nullable=True)    # open | closed | recovered | failed

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    actions = relationship("RecoveryAction", back_populates="case")
    audit_events = relationship("AuditEvent", back_populates="case", order_by="AuditEvent.timestamp")
