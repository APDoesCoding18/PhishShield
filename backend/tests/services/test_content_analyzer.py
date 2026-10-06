import pytest
from app.services.analyzers.content_analyzer import ContentAnalyzer
from app.schemas.analyzer import AnalysisContext
from app.models.analysis import Email

@pytest.fixture
def content_analyzer():
    return ContentAnalyzer()

def test_benign_content(content_analyzer):
    email = Email(
        id="test-1",
        subject="Lunch plans",
        body_text="Hey, are we still on for lunch tomorrow?"
    )
    context = AnalysisContext(job_id="job-1", workspace_path="/tmp", email_record=email)
    
    result = content_analyzer.analyze(context)
    
    assert result.status == "success"
    assert len(result.findings) == 0

def test_urgency_indicator(content_analyzer):
    email = Email(
        id="test-2",
        subject="Action Required: Update",
        body_text="Please do this immediately."
    )
    context = AnalysisContext(job_id="job-2", workspace_path="/tmp", email_record=email)
    
    result = content_analyzer.analyze(context)
    
    assert result.status == "success"
    assert len(result.findings) == 1
    assert result.findings[0].type == "urgency_indicator"
    assert set(result.findings[0].evidence["matched_phrases"]) == {"action required", "immediately"}

def test_credential_request_and_financial(content_analyzer):
    email = Email(
        id="test-3",
        subject="Overdue Invoice",
        body_text="Please verify your account to pay the invoice."
    )
    context = AnalysisContext(job_id="job-3", workspace_path="/tmp", email_record=email)
    
    result = content_analyzer.analyze(context)
    
    assert result.status == "success"
    # Should flag urgency (overdue), financial (invoice), and credential (verify your account)
    types = [f.type for f in result.findings]
    assert "urgency_indicator" in types
    assert "financial_indicator" in types
    assert "credential_request_indicator" in types
    assert len(result.findings) == 3

def test_case_insensitivity_and_punctuation(content_analyzer):
    email = Email(
        id="test-4",
        subject="Urgent!!!",
        body_text="VERIFY YOUR ACCOUNT NOW, Password..."
    )
    context = AnalysisContext(job_id="job-4", workspace_path="/tmp", email_record=email)
    
    result = content_analyzer.analyze(context)
    
    assert result.status == "success"
    types = [f.type for f in result.findings]
    assert "urgency_indicator" in types
    assert "credential_request_indicator" in types
    cred_finding = next(f for f in result.findings if f.type == "credential_request_indicator")
    assert "verify your account" in cred_finding.evidence["matched_phrases"]
    assert "password" in cred_finding.evidence["matched_phrases"]

def test_empty_content(content_analyzer):
    email = Email(
        id="test-5",
        subject="",
        body_text="",
        body_html=""
    )
    context = AnalysisContext(job_id="job-5", workspace_path="/tmp", email_record=email)
    
    result = content_analyzer.analyze(context)
    
    assert result.status == "success"
    assert len(result.findings) == 1
    assert result.findings[0].type == "empty_content"

def test_html_only_content(content_analyzer):
    email = Email(
        id="test-6",
        subject="",
        body_text="",
        body_html="<html><body>Please <b>login</b> immediately.</body></html>"
    )
    context = AnalysisContext(job_id="job-6", workspace_path="/tmp", email_record=email)
    
    result = content_analyzer.analyze(context)
    
    assert result.status == "success"
    types = [f.type for f in result.findings]
    assert "credential_request_indicator" in types
    assert "urgency_indicator" in types

def test_exception_handling(content_analyzer):
    # Pass an invalid context without email_record
    context = AnalysisContext(job_id="job-7", workspace_path="/tmp", email_record=None)
    
    result = content_analyzer.analyze(context)
    
    assert result.status == "error"
    assert "Content Analysis failed" in result.warnings[0]
