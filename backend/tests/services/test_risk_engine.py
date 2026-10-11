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

def _create_mock_finding(job_id, type_str, severity, title, category="mock", confidence="high"):
    return Finding(
        id=str(uuid.uuid4()),
        job_id=job_id,
        analyzer_name="MockAnalyzer",
        source="MockAnalyzer",
        category=category,
        finding_type=type_str,
        severity=severity,
        confidence=confidence,
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

def test_risk_engine_multiple_distinct_findings(db):
    job_id = _setup_mock_job(db)
    f1 = _create_mock_finding(job_id, "f1", "low", "Low Ind", category="cat1")
    f2 = _create_mock_finding(job_id, "f2", "medium", "Med Ind", category="cat2")
    
    engine = RiskEngine()
    result = engine.analyze(db, job_id, [f1, f2])
    
    assert result.score == 4.0
    assert result.severity == "low"
    assert result.verdict == "suspicious"

def test_risk_engine_25_excessive_encoding_findings_not_malicious(db):
    """
    CRITICAL REGRESSION TEST:
    An email with SPF/DKIM/DMARC pass and 25 repeated 'Excessive URL Encoding' medium findings
    must NOT produce a run-away 75+ score or a Malicious verdict.
    Instead, it groups the 25 findings into one root cause with diminishing returns,
    capping the group score and keeping verdict as Suspicious.
    """
    job_id = _setup_mock_job(db)
    findings = [
        _create_mock_finding(job_id, "spf_pass", "info", "SPF Passed", category="authentication"),
        _create_mock_finding(job_id, "dkim_pass", "info", "DKIM Passed", category="authentication"),
        _create_mock_finding(job_id, "dmarc_pass", "info", "DMARC Passed", category="authentication"),
    ]
    # Add 25 repeated URL encoding findings
    for i in range(25):
        findings.append(
            _create_mock_finding(
                job_id, 
                "excessive_encoding", 
                "medium", 
                "Excessive URL Encoding", 
                category="url_analysis"
            )
        )
        
    engine = RiskEngine()
    result = engine.analyze(db, job_id, findings)
    
    # 25 medium findings in the same group must cap at GROUP_CAPS['medium'] = 6.0
    assert result.score <= 6.0
    assert result.verdict == "suspicious"
    assert result.verdict != "malicious"
    assert "Excessive URL Encoding (25x)" in result.rationale

def test_risk_engine_attachment_critical(db):
    job_id = _setup_mock_job(db)
    f_att = _create_mock_finding(
        job_id, 
        "executable_attachment", 
        "critical", 
        "Executable Attachment",
        category="attachment_analysis"
    )
    
    engine = RiskEngine()
    result = engine.analyze(db, job_id, [f_att])
    
    assert result.score == 10.0
    assert result.severity == "medium"
    assert result.verdict == "malicious"
    assert "Direct weaponized or malicious artifact detected" in result.rationale

def test_risk_engine_credential_and_deceit_corroboration(db):
    """Corroborated phishing: credential harvest + auth failure produces Malicious verdict."""
    job_id = _setup_mock_job(db)
    f_cred = _create_mock_finding(
        job_id,
        "credential_request_indicator",
        "high",
        "Suspicious Credential Request",
        category="content"
    )
    f_auth = _create_mock_finding(
        job_id,
        "dmarc_fail",
        "high",
        "DMARC Failed",
        category="authentication"
    )
    
    engine = RiskEngine()
    result = engine.analyze(db, job_id, [f_cred, f_auth])
    
    assert result.score == 12.0
    assert result.verdict == "malicious"
    assert "Corroborated phishing attack" in result.rationale

def test_risk_engine_rationale_truncation(db):
    job_id = _setup_mock_job(db)
    findings = []
    for i in range(5):
        findings.append(
            _create_mock_finding(job_id, f"f{i}", "high", f"Indicator {i}", category=f"cat{i}")
        )
        
    engine = RiskEngine()
    result = engine.analyze(db, job_id, findings)
    
    # Should only show top 3 in summary
    assert "+ 2 other factor groups" in result.rationale
