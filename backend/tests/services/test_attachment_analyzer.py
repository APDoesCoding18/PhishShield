import os
import pytest
import hashlib
from app.schemas.analyzer import AnalysisContext
from app.services.analyzers.attachment_analyzer import AttachmentAnalyzer
from app.models.analysis import Attachment, Email

class DummyEmailRecord:
    def __init__(self, id):
        self.id = id

def _setup_mock_attachment(db, tmp_path, filename, content, mime_type="application/octet-stream"):
    email = Email(id="test_email", job_id="test_job", storage_filename="email.eml")
    db.add(email)
    db.commit()
    
    storage_name = f"att_{filename}"
    filepath = os.path.join(tmp_path, storage_name)
    with open(filepath, "wb") as f:
        f.write(content)
        
    sha256 = hashlib.sha256(content).hexdigest()
        
    att = Attachment(
        email_id=email.id,
        original_filename=filename,
        storage_filename=storage_name,
        mime_type=mime_type,
        size=len(content),
        sha256=sha256
    )
    db.add(att)
    db.commit()
    
    return email

def test_attachment_analyzer_normal_pdf(db, tmp_path):
    # Magic bytes for PDF
    content = b"%PDF-1.4 ... fake pdf content"
    email = _setup_mock_attachment(db, tmp_path, "document.pdf", content, "application/pdf")
    ctx = AnalysisContext(job_id="test", workspace_path=str(tmp_path), email_record=DummyEmailRecord(email.id))
    ctx.db = db
    
    analyzer = AttachmentAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    assert len(res.findings) == 0
    
    db_att = db.query(Attachment).first()
    assert db_att.detected_mime_type == "application/pdf"
    assert db_att.is_executable is False

def test_attachment_analyzer_executable(db, tmp_path):
    # MZ magic bytes
    content = b"MZ\x90\x00\x03\x00\x00\x00... executable content"
    email = _setup_mock_attachment(db, tmp_path, "update.exe", content, "application/x-msdownload")
    ctx = AnalysisContext(job_id="test", workspace_path=str(tmp_path), email_record=DummyEmailRecord(email.id))
    ctx.db = db
    
    analyzer = AttachmentAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    types = [f.type for f in res.findings]
    assert "executable_attachment" in types

def test_attachment_analyzer_mime_mismatch(db, tmp_path):
    # It's an EXE but claims to be PDF
    content = b"MZ\x90\x00\x03\x00\x00\x00..."
    email = _setup_mock_attachment(db, tmp_path, "invoice.pdf", content, "application/pdf")
    ctx = AnalysisContext(job_id="test", workspace_path=str(tmp_path), email_record=DummyEmailRecord(email.id))
    ctx.db = db
    
    analyzer = AttachmentAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    types = [f.type for f in res.findings]
    assert "executable_attachment" in types
    assert "mime_mismatch" in types
    assert "suspicious_filename" in types # Because it's an exe named "invoice"

def test_attachment_analyzer_double_extension(db, tmp_path):
    content = b"MZ..."
    email = _setup_mock_attachment(db, tmp_path, "receipt.pdf.exe", content, "application/x-msdownload")
    ctx = AnalysisContext(job_id="test", workspace_path=str(tmp_path), email_record=DummyEmailRecord(email.id))
    ctx.db = db
    
    analyzer = AttachmentAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    types = [f.type for f in res.findings]
    assert "double_extension" in types
    assert "suspicious_filename" in types # receipt + exe

def test_attachment_analyzer_large_file(db, tmp_path):
    # Just mock the DB record size to be huge, but don't actually write 11MB to disk for testing speed
    content = b"%PDF..."
    email = _setup_mock_attachment(db, tmp_path, "large.pdf", content, "application/pdf")
    
    db_att = db.query(Attachment).first()
    db_att.size = 15000000 # 15MB
    db.commit()
    
    ctx = AnalysisContext(job_id="test", workspace_path=str(tmp_path), email_record=DummyEmailRecord(email.id))
    ctx.db = db
    
    analyzer = AttachmentAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    types = [f.type for f in res.findings]
    assert "large_attachment" in types

def test_attachment_analyzer_archive(db, tmp_path):
    content = b"PK\x03\x04..."
    email = _setup_mock_attachment(db, tmp_path, "urgent_docs.zip", content, "application/zip")
    ctx = AnalysisContext(job_id="test", workspace_path=str(tmp_path), email_record=DummyEmailRecord(email.id))
    ctx.db = db
    
    analyzer = AttachmentAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    types = [f.type for f in res.findings]
    assert "archive_attachment" in types
    assert "suspicious_filename" in types # urgent + zip

def test_attachment_analyzer_malformed_file(db, tmp_path):
    # Empty file or unreadable
    email = _setup_mock_attachment(db, tmp_path, "empty.txt", b"", "text/plain")
    ctx = AnalysisContext(job_id="test", workspace_path=str(tmp_path), email_record=DummyEmailRecord(email.id))
    ctx.db = db
    
    analyzer = AttachmentAnalyzer()
    res = analyzer.analyze(ctx)
    
    assert res.status == "success"
    db_att = db.query(Attachment).first()
    assert db_att.detected_mime_type == "application/octet-stream"
