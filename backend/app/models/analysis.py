import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Text, Integer, Boolean
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base

class JobStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # workspace path relative to configured uploads directory
    workspace_path = Column(String, nullable=False)
    
    # Relationships
    emails = relationship("Email", back_populates="job", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="job", cascade="all, delete-orphan")


class Email(Base):
    __tablename__ = "emails"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("analysis_jobs.id"), nullable=False)
    
    # The generated safe filename (e.g. email.eml) inside the workspace
    storage_filename = Column(String, nullable=False)
    
    # The original filename, untrusted, for reference only
    original_filename = Column(String, nullable=True)
    
    # Parsed metadata
    sender = Column(String, nullable=True)
    recipient = Column(String, nullable=True)
    cc = Column(String, nullable=True)
    reply_to = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    date_header = Column(String, nullable=True)
    message_id = Column(String, nullable=True)
    
    # Body
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    
    # Parsing status
    is_parsed = Column(String, default="false", nullable=False) # e.g. "false", "true", "error"
    parsing_error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    job = relationship("AnalysisJob", back_populates="emails")
    attachments = relationship("Attachment", back_populates="email", cascade="all, delete-orphan")
    urls = relationship("URL", back_populates="email", cascade="all, delete-orphan")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email_id = Column(String, ForeignKey("emails.id"), nullable=False)
    
    original_filename = Column(String, nullable=True)
    storage_filename = Column(String, nullable=False)
    mime_type = Column(String, nullable=True)
    detected_mime_type = Column(String, nullable=True)
    is_executable = Column(Boolean, default=False)
    size = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    email = relationship("Email", back_populates="attachments")


class URL(Base):
    __tablename__ = "urls"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email_id = Column(String, ForeignKey("emails.id"), nullable=False)
    
    url = Column(Text, nullable=False)
    source = Column(String, nullable=False)  # e.g., 'body_text', 'body_html', 'header'
    
    normalized_url = Column(Text, nullable=True)
    domain = Column(String, nullable=True)
    scheme = Column(String, nullable=True)
    port = Column(Integer, nullable=True)
    is_ip = Column(Boolean, default=False)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    email = relationship("Email", back_populates="urls")
