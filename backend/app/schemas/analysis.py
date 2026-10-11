from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from app.models.analysis import JobStatus

class AnalysisJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    
    class Config:
        from_attributes = True

class AnalysisJobDetailResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    created_at: datetime
    updated_at: datetime

class AnalysisHistoryItemResponse(BaseModel):
    job_id: str
    original_filename: Optional[str] = None
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    verdict: Optional[str] = None
    score: Optional[float] = None
    severity: Optional[str] = None

class FindingResponse(BaseModel):
    type: str
    category: str
    severity: str
    title: str
    description: Optional[str]
    evidence: Optional[str]

class RiskResultResponse(BaseModel):
    verdict: str
    score: float
    severity: str
    rationale: str
    findings: List[FindingResponse]

class EmailResponse(BaseModel):
    sender: Optional[str]
    recipient: Optional[str]
    subject: Optional[str]
    date_header: Optional[str]
    body_text: Optional[str]
    body_html: Optional[str]

class UrlResponse(BaseModel):
    url: str
    normalized_url: Optional[str]
    domain: Optional[str]
    is_ip: bool

class AttachmentResponse(BaseModel):
    original_filename: Optional[str]
    mime_type: Optional[str]
    detected_mime_type: Optional[str]
    is_executable: bool
    size: int
    sha256: str
