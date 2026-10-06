import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship

from app.core.database import Base

class RiskResult(Base):
    __tablename__ = "risk_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("analysis_jobs.id"), nullable=False, unique=True)
    
    score = Column(Float, nullable=False)
    severity = Column(String, nullable=False)  # informational, low, medium, high, critical
    verdict = Column(String, nullable=False)   # clean, suspicious, malicious, unknown, error
    rationale = Column(Text, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Use back_populates on AnalysisJob side if defined, or backref
    job = relationship("AnalysisJob", backref="risk_result")
