import os
import uuid
import shutil
import logging
from typing import Tuple
from fastapi import UploadFile, HTTPException

from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.analysis import AnalysisJob, Email, JobStatus
from app.models.audit import AuditEvent

logger = logging.getLogger(__name__)

class UploadException(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code


def secure_upload_email(db: Session, file: UploadFile) -> AnalysisJob:
    """
    Handles secure upload of email files, enforces validations,
    creates isolated workspace, and records job and audit info.
    """
    # 1. Validate Extension
    if not file.filename:
        raise UploadException("INVALID_FILENAME", "Filename is required")
        
    ext = os.path.splitext(file.filename)[1].lower()
    if ext != ".eml":
        raise UploadException("UNSUPPORTED_FORMAT", "Only .eml files are supported for this milestone")

    # 2. Validate MIME Type (basic check)
    allowed_mimes = ["message/rfc822", "text/plain", "application/octet-stream"]
    if file.content_type not in allowed_mimes:
        raise UploadException("INVALID_MIME_TYPE", f"MIME type {file.content_type} is not permitted")

    # 3. Create unique Job ID and Workspace
    job_id = str(uuid.uuid4())
    
    # Path traversal protection is inherently handled by using a new UUID for the folder
    # and ignoring the user's filename for the actual storage path.
    workspace_name = f"job_{job_id}"
    workspace_path = os.path.join(settings.UPLOAD_DIRECTORY, workspace_name)
    
    try:
        os.makedirs(workspace_path, exist_ok=False)
    except Exception as e:
        logger.error(f"Failed to create workspace {workspace_path}: {e}")
        raise UploadException("INTERNAL_ERROR", "Failed to initialize secure workspace", 500)

    # 4. Generate safe server-side storage name
    storage_filename = "email.eml"
    storage_path = os.path.join(workspace_path, storage_filename)

    # 5. Save the file and enforce MAX_UPLOAD_SIZE
    saved_bytes = 0
    try:
        with open(storage_path, "wb") as buffer:
            # Chunked read to enforce size limit dynamically without loading entire file in memory
            while True:
                chunk = file.file.read(8192)
                if not chunk:
                    break
                saved_bytes += len(chunk)
                if saved_bytes > settings.MAX_UPLOAD_SIZE:
                    raise UploadException("FILE_TOO_LARGE", f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE} bytes")
                buffer.write(chunk)
                
    except UploadException:
        # Cleanup partial file/workspace on size limit
        shutil.rmtree(workspace_path, ignore_errors=True)
        raise
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        shutil.rmtree(workspace_path, ignore_errors=True)
        raise UploadException("INTERNAL_ERROR", "Failed to save uploaded file", 500)
    finally:
        file.file.close()

    # 6. Create Database Records
    try:
        job = AnalysisJob(id=job_id, status=JobStatus.PENDING, workspace_path=workspace_path)
        db.add(job)
        
        email_record = Email(
            job_id=job_id,
            storage_filename=storage_filename,
            original_filename=file.filename
        )
        db.add(email_record)
        
        audit_event = AuditEvent(
            job_id=job_id,
            event_type="UPLOAD_ACCEPTED",
            details=f"Email uploaded successfully. Size: {saved_bytes} bytes."
        )
        db.add(audit_event)
        
        db.commit()
        db.refresh(job)
        return job
    except Exception as e:
        db.rollback()
        logger.error(f"Database error during upload: {e}")
        shutil.rmtree(workspace_path, ignore_errors=True)
        raise UploadException("DATABASE_ERROR", "Failed to create analysis job records", 500)
