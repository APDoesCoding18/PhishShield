import pytest
import os
from app.workers.orchestrator import run_analysis_pipeline
from app.models.analysis import AnalysisJob, Email, JobStatus
from app.models.risk import RiskResult

def test_run_analysis_pipeline(db, tmp_path):
    # Setup mock job
    job_id = "test-job-123"
    workspace = str(tmp_path)
    job = AnalysisJob(id=job_id, workspace_path=workspace, status=JobStatus.PENDING)
    db.add(job)
    
    # Needs a real file to not fail parsing entirely
    eml_path = os.path.join(workspace, "email.eml")
    with open(eml_path, "wb") as f:
        f.write(b"Subject: Test\n\nBody")
        
    email = Email(
        id="test-email-123",
        job_id=job_id,
        storage_filename="email.eml"
    )
    db.add(email)
    db.commit()
    
    from unittest.mock import patch, MagicMock
    
    # We create a mock that returns the test db but doesn't do anything on close()
    # since pytest manages the db session.
    mock_session = MagicMock()
    mock_session.query = db.query
    mock_session.add = db.add
    mock_session.commit = db.commit
    mock_session.rollback = db.rollback
    mock_session.close = lambda: None
    
    # Run the pipeline (sync call for testing)
    with patch("app.workers.orchestrator.SessionLocal", return_value=mock_session):
        run_analysis_pipeline(job_id)
    
    # Check job status is completed
    updated_job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    assert updated_job.status == JobStatus.COMPLETED
    
    # Check risk result exists
    risk = db.query(RiskResult).filter(RiskResult.job_id == job_id).first()
    assert risk is not None
    assert risk.verdict in ("clean", "suspicious", "malicious")  # Depends on the engine's default rules
