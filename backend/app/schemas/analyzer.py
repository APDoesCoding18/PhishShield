from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

class FindingSchema(BaseModel):
    source: str
    category: str
    type: str
    severity: str
    confidence: str
    title: str
    description: str
    evidence: Optional[Dict[str, Any]] = None
    artifact_ref: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AnalysisResult(BaseModel):
    analyzer_name: str
    analyzer_version: str
    status: str # e.g. "success", "error", "skipped"
    findings: List[FindingSchema] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)
    raw_results: Optional[Dict[str, Any]] = None

class AnalysisContext:
    """
    Provides analyzers with isolated access to the job's context,
    workspace, and shared metadata without coupling them to the pipeline.
    """
    def __init__(self, job_id: str, workspace_path: str, email_record):
        self.job_id = job_id
        self.workspace_path = workspace_path
        self.email_record = email_record
