import os
import shutil
import pytest
from app.core.config import settings
from app.models.analysis import AnalysisJob, Email, JobStatus
from app.models.audit import AuditEvent

@pytest.fixture(autouse=True)
def setup_teardown():
    # Setup: ensure uploads directory is clean
    if os.path.exists(settings.UPLOAD_DIRECTORY):
        shutil.rmtree(settings.UPLOAD_DIRECTORY)
    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
    yield
    # Teardown
    if os.path.exists(settings.UPLOAD_DIRECTORY):
        shutil.rmtree(settings.UPLOAD_DIRECTORY)

@pytest.fixture(autouse=True)
def mock_celery_delay():
    with patch("app.api.v1.endpoints.analyses.run_analysis_pipeline.delay") as mock:
        yield mock

from unittest.mock import patch

def test_valid_eml_upload(client, db, mock_celery_delay):
    file_content = b"Subject: Test Phishing Email\n\nThis is a test."
    files = {"file": ("test_email.eml", file_content, "message/rfc822")}
    
    response = client.post(f"{settings.API_V1_PREFIX}/analyses", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "PENDING"
    
    # Verify celery was called
    mock_celery_delay.assert_called_once_with(data["job_id"])
    
    # Verify Database Models
    job_id = data["job_id"]
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    assert job is not None
    
    email = db.query(Email).filter(Email.job_id == job_id).first()
    assert email is not None
    assert email.original_filename == "test_email.eml"
    assert email.storage_filename == "email.eml"
    
    audit = db.query(AuditEvent).filter(AuditEvent.job_id == job_id).first()
    assert audit is not None
    assert audit.event_type == "UPLOAD_ACCEPTED"
    
    # Verify file is on disk in isolated workspace
    workspace = job.workspace_path
    assert os.path.isdir(workspace)
    assert os.path.exists(os.path.join(workspace, "email.eml"))

def test_unsupported_extension(client):
    files = {"file": ("malware.exe", b"MZ...", "application/octet-stream")}
    response = client.post(f"{settings.API_V1_PREFIX}/analyses", files=files)
    
    assert response.status_code == 400
    assert response.json()["error_code"] == "UNSUPPORTED_FORMAT"

def test_oversized_file(client, monkeypatch):
    # Temporarily set max upload size to 10 bytes
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 10)
    
    files = {"file": ("large.eml", b"This file is definitely larger than 10 bytes", "message/rfc822")}
    response = client.post(f"{settings.API_V1_PREFIX}/analyses", files=files)
    
    assert response.status_code == 400
    assert response.json()["error_code"] == "FILE_TOO_LARGE"
    
def test_mime_mismatch(client):
    # Eml file extension but invalid mime type
    files = {"file": ("test.eml", b"content", "image/png")}
    response = client.post(f"{settings.API_V1_PREFIX}/analyses", files=files)
    
    assert response.status_code == 400
    assert response.json()["error_code"] == "INVALID_MIME_TYPE"

def test_path_traversal_filename(client):
    # Test that dangerous filenames don't result in path traversal
    # Our service generates its own UUID workspace and "email.eml", ignoring the input filename for path construction.
    files = {"file": ("../../../etc/passwd.eml", b"content", "message/rfc822")}
    response = client.post(f"{settings.API_V1_PREFIX}/analyses", files=files)
    
    assert response.status_code == 200
    data = response.json()
    job_id = data["job_id"]
    
    # Check that it didn't write to /etc/passwd but safely in the workspace
    workspace_path = os.path.join(settings.UPLOAD_DIRECTORY, f"job_{job_id}")
    assert os.path.exists(os.path.join(workspace_path, "email.eml"))
