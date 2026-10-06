import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.core.database import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("analysis_jobs.id"), nullable=True)
    
    event_type = Column(String, nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    job = relationship("AnalysisJob", back_populates="audit_events")
