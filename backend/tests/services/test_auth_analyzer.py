import os
import pytest
from email.message import EmailMessage

from app.schemas.analyzer import AnalysisContext
from app.services.analyzers.auth_analyzer import AuthenticationAnalyzer
from app.models.analysis import AnalysisJob, Email

class DummyEmailRecord:
    def __init__(self, storage_filename):
        self.storage_filename = storage_filename

def _create_mock_context(tmp_path, headers=None, filename="email.eml"):
    eml_path = os.path.join(tmp_path, filename)
    msg = EmailMessage()
    if headers:
        for k, v in headers:
            msg[k] = v
    with open(eml_path, 'wb') as f:
        f.write(bytes(msg))
        
    return AnalysisContext(job_id="test", workspace_path=str(tmp_path), email_record=DummyEmailRecord(filename))

def test_auth_analyzer_missing_headers(tmp_path):
    ctx = _create_mock_context(tmp_path, headers=[("Subject", "Test")])
    analyzer = AuthenticationAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    assert len(res.findings) == 1
    assert res.findings[0].type == "missing_headers"
    
def test_auth_analyzer_all_pass(tmp_path):
    auth_header = "mx.google.com; dkim=pass header.i=@test.com; spf=pass (domain designates 1.2.3.4); dmarc=pass"
    ctx = _create_mock_context(tmp_path, headers=[("Authentication-Results", auth_header)])
    analyzer = AuthenticationAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    types = [f.type for f in res.findings]
    assert "spf_pass" in types
    assert "dkim_pass" in types
    assert "dmarc_pass" in types

def test_auth_analyzer_failures(tmp_path):
    auth_header = "mx.google.com; dkim=fail; spf=softfail; dmarc=fail"
    ctx = _create_mock_context(tmp_path, headers=[("Authentication-Results", auth_header)])
    analyzer = AuthenticationAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    types = [f.type for f in res.findings]
    assert "spf_fail" in types
    assert "dkim_fail" in types
    assert "dmarc_fail" in types
    
def test_auth_analyzer_none_neutral(tmp_path):
    auth_header = "mx.google.com; dkim=none; spf=neutral; dmarc=none"
    ctx = _create_mock_context(tmp_path, headers=[("Authentication-Results", auth_header)])
    analyzer = AuthenticationAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    types = [f.type for f in res.findings]
    assert "spf_neutral" in types
    assert "dkim_neutral" in types
    assert "dmarc_neutral" in types

def test_auth_analyzer_file_missing(tmp_path):
    ctx = AnalysisContext(job_id="test", workspace_path=str(tmp_path), email_record=DummyEmailRecord("missing.eml"))
    analyzer = AuthenticationAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "error"
    assert "not found" in res.warnings[0]
