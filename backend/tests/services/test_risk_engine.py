import pytest
from app.services.risk_engine import RiskEngine
from app.models.finding import Finding
from app.models.analysis import AnalysisJob
import uuid

def _setup_mock_job(db):
    job_id = str(uuid.uuid4())
    job = AnalysisJob(id=job_id, workspace_path="/dev/null")
    db.add(job)
    db.commit()
    return job_id

def _create_mock_finding(job_id, type_str, severity, title):
    return Finding(
        id=str(uuid.uuid4()),
        job_id=job_id,
        analyzer_name="MockAnalyzer",
        source="MockAnalyzer",
        category="mock",
        finding_type=type_str,
        severity=severity,
        confidence="high",
        title=title
    )

def test_risk_engine_no_findings(db):
    job_id = _setup_mock_job(db)
    engine = RiskEngine()
    result = engine.analyze(db, job_id, [])
    
    assert result.score == 0.0
    assert result.severity == "informational"
    assert result.verdict == "clean"
    assert "No suspicious indicators" in result.rationale

def test_risk_engine_single_low_finding(db):
    job_id = _setup_mock_job(db)
    finding = _create_mock_finding(job_id, "suspicious_domain", "low", "Excessive Subdomains")
    
    engine = RiskEngine()
    result = engine.analyze(db, job_id, [finding])
    
    assert result.score == 1.0
    assert result.severity == "low"
    assert result.verdict == "suspicious"
    assert "Excessive Subdomains" in result.rationale

def test_risk_engine_multiple_findings(db):
    job_id = _setup_mock_job(db)
    f1 = _create_mock_finding(job_id, "f1", "low", "Low Ind")
    f2 = _create_mock_finding(job_id, "f2", "medium", "Med Ind")
    
    engine = RiskEngine()
    result = engine.analyze(db, job_id, [f1, f2])
    
    assert result.score == 4.0
    assert result.severity == "medium"
    assert result.verdict == "suspicious"

def test_risk_engine_auth_and_url_findings(db):
    job_id = _setup_mock_job(db)
    f_auth = _create_mock_finding(job_id, "spf_fail", "high", "SPF Failed")
    f_url = _create_mock_finding(job_id, "ip_url", "high", "IP URL")
    
    engine = RiskEngine()
    result = engine.analyze(db, job_id, [f_auth, f_url])
    
    assert result.score == 12.0
    assert result.severity == "critical"
    assert result.verdict == "malicious"
    assert "SPF Failed" in result.rationale
    assert "IP URL" in result.rationale

def test_risk_engine_attachment_critical(db):
    job_id = _setup_mock_job(db)
    f_att = _create_mock_finding(job_id, "executable_attachment", "critical", "Executable Attachment")
    
    engine = RiskEngine()
    result = engine.analyze(db, job_id, [f_att])
    
    assert result.score == 10.0
    assert result.severity == "critical"
    assert result.verdict == "malicious"

def test_risk_engine_rationale_truncation(db):
    job_id = _setup_mock_job(db)
    findings = []
    for i in range(5):
        findings.append(_create_mock_finding(job_id, f"f{i}", "high", f"Indicator {i}"))
        
    engine = RiskEngine()
    result = engine.analyze(db, job_id, findings)
    
    assert result.score == 30.0
    assert result.severity == "critical"
    # Should only show top 3
    assert "+ 2 other findings" in result.rationale
