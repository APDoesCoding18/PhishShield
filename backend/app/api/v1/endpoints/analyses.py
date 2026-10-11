from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.models.analysis import AnalysisJob, Email, Attachment, URL, JobStatus
from app.models.risk import RiskResult
from app.models.finding import Finding
from app.schemas.analysis import (
    AnalysisJobResponse, AnalysisJobDetailResponse, AnalysisHistoryItemResponse,
    RiskResultResponse, FindingResponse, EmailResponse, UrlResponse, AttachmentResponse
)
from app.schemas.error import ErrorResponse
from app.services.upload import secure_upload_email, UploadException
from app.workers.orchestrator import run_analysis_pipeline
from typing import List, Optional

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("", response_model=List[AnalysisHistoryItemResponse])
def list_analysis_history(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Returns real persisted analysis records with filenames, status, timestamps, and verdicts.
    """
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    query = db.query(AnalysisJob)
    if status:
        query = query.filter(AnalysisJob.status == status.upper())

    jobs = query.order_by(AnalysisJob.created_at.desc()).offset(offset).limit(limit).all()

    results: List[AnalysisHistoryItemResponse] = []
    for job in jobs:
        # Get associated email for original filename
        email_record = db.query(Email).filter(Email.job_id == job.id).first()
        # Get risk result if completed
        risk = db.query(RiskResult).filter(RiskResult.job_id == job.id).first()

        results.append(
            AnalysisHistoryItemResponse(
                job_id=job.id,
                original_filename=email_record.original_filename if email_record else None,
                status=job.status,
                created_at=job.created_at,
                updated_at=job.updated_at,
                verdict=risk.verdict if risk else None,
                score=risk.score if risk else None,
                severity=risk.severity if risk else None,
            )
        )

    return results

@router.post("", response_model=AnalysisJobResponse, responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}})
def create_analysis_job(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Securely uploads an email and creates a new analysis job.
    """
    try:
        job = secure_upload_email(db=db, file=file)
        
        # Enqueue background orchestration
        run_analysis_pipeline.delay(job.id)
        
        return AnalysisJobResponse(job_id=job.id, status=job.status)
    except UploadException as e:
        logger.warning(f"Upload failed: {e.code} - {e.message}")
        error = ErrorResponse(error_code=e.code, message=e.message)
        return JSONResponse(status_code=e.status_code, content=error.model_dump())
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        error = ErrorResponse(error_code="INTERNAL_ERROR", message="An unexpected error occurred during processing.")
        return JSONResponse(status_code=500, content=error.model_dump())

@router.get("/{job_id}", response_model=AnalysisJobDetailResponse, responses={404: {"model": ErrorResponse}})
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if not job:
        return JSONResponse(status_code=404, content=ErrorResponse(error_code="NOT_FOUND", message="Job not found").model_dump())
    
    progress = 0
    if job.status == JobStatus.COMPLETED:
        progress = 100
    elif job.status == JobStatus.PROCESSING:
        progress = 50
    elif job.status == JobStatus.FAILED:
        progress = 0
        
    return AnalysisJobDetailResponse(
        job_id=job.id,
        status=job.status,
        progress=progress,
        created_at=job.created_at,
        updated_at=job.updated_at
    )

@router.get("/{job_id}/result", response_model=RiskResultResponse, responses={404: {"model": ErrorResponse}})
def get_job_result(job_id: str, db: Session = Depends(get_db)):
    risk = db.query(RiskResult).filter(RiskResult.job_id == job_id).first()
    if not risk:
        return JSONResponse(status_code=404, content=ErrorResponse(error_code="NOT_FOUND", message="Result not available yet").model_dump())
        
    findings = db.query(Finding).filter(Finding.job_id == job_id).all()
    finding_responses = [
        FindingResponse(
            type=f.finding_type,
            category=f.category,
            severity=f.severity,
            title=f.title,
            description=f.description,
            evidence=f.evidence
        ) for f in findings
    ]
    
    return RiskResultResponse(
        verdict=risk.verdict,
        score=risk.score,
        severity=risk.severity,
        rationale=risk.rationale,
        findings=finding_responses
    )

@router.get("/{job_id}/email", response_model=EmailResponse, responses={404: {"model": ErrorResponse}})
def get_job_email(job_id: str, db: Session = Depends(get_db)):
    email_rec = db.query(Email).filter(Email.job_id == job_id).first()
    if not email_rec:
        return JSONResponse(status_code=404, content=ErrorResponse(error_code="NOT_FOUND", message="Email record not found").model_dump())
    
    return EmailResponse(
        sender=email_rec.sender,
        recipient=email_rec.recipient,
        subject=email_rec.subject,
        date_header=email_rec.date_header,
        body_text=email_rec.body_text,
        body_html=email_rec.body_html
    )

@router.get("/{job_id}/urls", response_model=list[UrlResponse])
def get_job_urls(job_id: str, db: Session = Depends(get_db)):
    email_rec = db.query(Email).filter(Email.job_id == job_id).first()
    if not email_rec:
        return []
    
    urls = db.query(URL).filter(URL.email_id == email_rec.id).all()
    return [
        UrlResponse(
            url=u.url,
            normalized_url=u.normalized_url,
            domain=u.domain,
            is_ip=u.is_ip
        ) for u in urls
    ]

@router.get("/{job_id}/attachments", response_model=list[AttachmentResponse])
def get_job_attachments(job_id: str, db: Session = Depends(get_db)):
    email_rec = db.query(Email).filter(Email.job_id == job_id).first()
    if not email_rec:
        return []
    
    attachments = db.query(Attachment).filter(Attachment.email_id == email_rec.id).all()
    return [
        AttachmentResponse(
            original_filename=a.original_filename,
            mime_type=a.mime_type,
            detected_mime_type=a.detected_mime_type,
            is_executable=a.is_executable,
            size=a.size,
            sha256=a.sha256
        ) for a in attachments
    ]
