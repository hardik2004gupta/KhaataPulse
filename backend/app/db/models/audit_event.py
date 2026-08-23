from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class AuditEvent(Base):
    """
    Immutable audit trail — CLAUDE.md §16.

    Every meaningful decision produces one record. Append-only: rows are never
    updated or deleted. The payload preserves the structured information required
    for reconstruction.
    """
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(
        Integer, ForeignKey("recovery_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type = Column(String(50), nullable=False)
    # Required event types: risk_detected | diagnosis_generated | action_proposed |
    #                        policy_check | action_executed | payment_received |
    #                        case_closed | llm_fallback
    actor = Column(String(100), nullable=False)    # which module/system produced this event
    payload = Column(JSON, nullable=False)          # structured reconstruction data
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    idempotency_key = Column(String(100), nullable=True)

    case = relationship("RecoveryCase", back_populates="audit_events")
