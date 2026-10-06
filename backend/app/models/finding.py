import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base

class Finding(Base):
    __tablename__ = "findings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("analysis_jobs.id"), nullable=False)
    
    analyzer_name = Column(String, nullable=False)
    source = Column(String, nullable=False)
    category = Column(String, nullable=False)
    finding_type = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    confidence = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    evidence = Column(Text, nullable=True)  # Store as JSON string since we use sqlite for testing
    artifact_ref = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    job = relationship("AnalysisJob", backref="findings")
