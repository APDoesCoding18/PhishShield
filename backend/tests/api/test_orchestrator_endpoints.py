import pytest
from app.models.analysis import AnalysisJob, Email, Attachment, URL, JobStatus
from app.models.risk import RiskResult
from app.models.finding import Finding
from app.core.config import settings
import uuid

def _setup_mock_data(db):
    job_id = str(uuid.uuid4())
    job = AnalysisJob(id=job_id, workspace_path="/dev/null", status=JobStatus.COMPLETED)
    db.add(job)
    
    email = Email(
        id=str(uuid.uuid4()),
        job_id=job_id,
        storage_filename="email.eml",
        sender="attacker@evil.com",
        subject="Urgent"
    )
    db.add(email)
    
    risk = RiskResult(
        job_id=job_id,
        score=10.0,
        severity="critical",
        verdict="malicious",
        rationale="Top finding: exe"
    )
    db.add(risk)
    
    finding = Finding(
        job_id=job_id,
        analyzer_name="Mock",
        source="Mock",
        category="mock",
        finding_type="exe",
        severity="critical",
        confidence="high",
        title="Exe found"
    )
    db.add(finding)
    
    att = Attachment(
        email_id=email.id,
        storage_filename="file.exe",
        original_filename="file.exe",
        size=1000,
        sha256="123",
        detected_mime_type="application/x-msdownload",
        is_executable=True
    )
    db.add(att)
    
    url = URL(
        email_id=email.id,
        url="http://evil.com",
        source="body",
        domain="evil.com",
        is_ip=False
    )
    db.add(url)
    
    db.commit()
    return job_id

def test_get_job_status(client, db):
    job_id = _setup_mock_data(db)
    res = client.get(f"{settings.API_V1_PREFIX}/analyses/{job_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["job_id"] == job_id
    assert data["status"] == "COMPLETED"
    assert data["progress"] == 100

def test_get_job_result(client, db):
    job_id = _setup_mock_data(db)
    res = client.get(f"{settings.API_V1_PREFIX}/analyses/{job_id}/result")
    assert res.status_code == 200
    data = res.json()
    assert data["verdict"] == "malicious"
    assert data["score"] == 10.0
    assert len(data["findings"]) == 1

def test_get_job_email(client, db):
    job_id = _setup_mock_data(db)
    res = client.get(f"{settings.API_V1_PREFIX}/analyses/{job_id}/email")
    assert res.status_code == 200
    data = res.json()
    assert data["sender"] == "attacker@evil.com"
    assert data["subject"] == "Urgent"

def test_get_job_urls(client, db):
    job_id = _setup_mock_data(db)
    res = client.get(f"{settings.API_V1_PREFIX}/analyses/{job_id}/urls")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["domain"] == "evil.com"

def test_get_job_attachments(client, db):
    job_id = _setup_mock_data(db)
    res = client.get(f"{settings.API_V1_PREFIX}/analyses/{job_id}/attachments")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 1
    assert data[0]["is_executable"] is True

def test_get_job_not_found(client):
    res = client.get(f"{settings.API_V1_PREFIX}/analyses/invalid-id")
    assert res.status_code == 404
