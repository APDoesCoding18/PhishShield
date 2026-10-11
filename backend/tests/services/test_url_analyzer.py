import pytest
from app.schemas.analyzer import AnalysisContext
from app.services.analyzers.url_analyzer import UrlAnalyzer
from app.models.analysis import URL, Email

class DummyEmailRecord:
    def __init__(self, id):
        self.id = id

def _setup_db_urls(db, url_strings):
    email = Email(id="test_email", job_id="test_job", storage_filename="email.eml")
    db.add(email)
    db.commit()
    
    for u in url_strings:
        db.add(URL(email_id=email.id, url=u, source="body_text"))
    db.commit()
    return email

def test_url_analyzer_normal(db):
    email = _setup_db_urls(db, ["https://www.google.com/search?q=test"])
    ctx = AnalysisContext(job_id="test", workspace_path="", email_record=DummyEmailRecord(email.id))
    ctx.db = db
    
    analyzer = UrlAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    assert len(res.findings) == 0
    
    db_url = db.query(URL).filter(URL.email_id == email.id).first()
    assert db_url.domain == "www.google.com"
    assert db_url.scheme == "https"
    assert db_url.port is None
    assert db_url.is_ip is False
    assert db_url.normalized_url == "https://www.google.com/search?q=test"

def test_url_analyzer_ip_based(db):
    email = _setup_db_urls(db, ["http://192.168.1.100/login"])
    ctx = AnalysisContext(job_id="test", workspace_path="", email_record=DummyEmailRecord(email.id))
    ctx.db = db
    
    analyzer = UrlAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    types = [f.type for f in res.findings]
    assert "ip_url" in types
    
    db_url = db.query(URL).filter(URL.email_id == email.id).first()
    assert db_url.is_ip is True

def test_url_analyzer_shortener(db):
    email = _setup_db_urls(db, ["http://bit.ly/123xyz"])
    ctx = AnalysisContext(job_id="test", workspace_path="", email_record=DummyEmailRecord(email.id))
    ctx.db = db
    
    analyzer = UrlAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    types = [f.type for f in res.findings]
    assert "url_shortener" in types

def test_url_analyzer_unusual_port_and_scheme(db):
    email = _setup_db_urls(db, ["ftp://files.example.com:2121/payload.exe"])
    ctx = AnalysisContext(job_id="test", workspace_path="", email_record=DummyEmailRecord(email.id))
    ctx.db = db
    
    analyzer = UrlAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    types = [f.type for f in res.findings]
    assert "unusual_port" in types
    assert "suspicious_scheme" in types

def test_url_analyzer_userinfo_and_subdomains(db):
    email = _setup_db_urls(db, ["https://paypal-support@secure.login.update.account.example.com/"])
    ctx = AnalysisContext(job_id="test", workspace_path="", email_record=DummyEmailRecord(email.id))
    ctx.db = db
    
    analyzer = UrlAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    types = [f.type for f in res.findings]
    assert "suspicious_userinfo" in types
    assert "excessive_subdomains" in types

def test_url_analyzer_excessive_encoding(db):
    # Lots of % characters and a %00 (null byte)
    url = "https://example.com/view?param=%20%20%20%20%20%20%20%20%20%20%20%00"
    email = _setup_db_urls(db, [url])
    ctx = AnalysisContext(job_id="test", workspace_path="", email_record=DummyEmailRecord(email.id))
    ctx.db = db
    
    analyzer = UrlAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    types = [f.type for f in res.findings]
    assert "excessive_encoding" in types
    assert "suspicious_encoding" in types

def test_url_analyzer_malformed(db):
    # Pass something that breaks standard parsing if possible, or test ValueError handling
    email = _setup_db_urls(db, ["http://[invalid-ipv6-bracket/"])
    ctx = AnalysisContext(job_id="test", workspace_path="", email_record=DummyEmailRecord(email.id))
    ctx.db = db
    
    analyzer = UrlAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    # urllib.parse.urlparse handles almost anything, but port parsing might raise ValueError on bad port brackets
    types = [f.type for f in res.findings]
    assert "malformed_url" in types
