import os
import pytest
from email.message import EmailMessage
from app.models.analysis import AnalysisJob, Email, Attachment, URL
from app.services.parser import parse_email_service
import hashlib

def _create_mock_job_and_email(db, workspace_path):
    os.makedirs(workspace_path, exist_ok=True)
    job = AnalysisJob(id="test_job", workspace_path=workspace_path)
    db.add(job)
    email_record = Email(id="test_email", job_id="test_job", storage_filename="email.eml")
    db.add(email_record)
    db.commit()
    return job, email_record

def test_plain_text_email(db, tmp_path):
    job, email_record = _create_mock_job_and_email(db, str(tmp_path))
    eml_path = os.path.join(tmp_path, email_record.storage_filename)
    
    msg = EmailMessage()
    msg['Subject'] = 'Test Plain Text'
    msg['From'] = 'alice@example.com'
    msg['To'] = 'bob@example.com'
    msg.set_content('This is a simple plain text body with a URL: http://example.com/test')
    
    with open(eml_path, 'wb') as f:
        f.write(bytes(msg))
        
    parse_email_service(db, email_record.id)
    
    db.refresh(email_record)
    assert email_record.is_parsed == "true"
    assert email_record.subject == "Test Plain Text"
    assert email_record.sender == "alice@example.com"
    assert email_record.recipient == "bob@example.com"
    assert "This is a simple plain text body" in email_record.body_text
    
    urls = db.query(URL).filter(URL.email_id == email_record.id).all()
    assert len(urls) == 1
    assert urls[0].url == "http://example.com/test"

def test_multipart_email_with_html_and_attachment(db, tmp_path):
    job, email_record = _create_mock_job_and_email(db, str(tmp_path))
    eml_path = os.path.join(tmp_path, email_record.storage_filename)
    
    msg = EmailMessage()
    msg['Subject'] = 'Test Multipart'
    msg['From'] = 'sender@test.com'
    
    msg.add_alternative("Plain body", subtype='plain')
    msg.add_alternative("<html><body>HTML body with https://secure.com</body></html>", subtype='html')
    
    attachment_content = b'MZ_fake_exe_content'
    msg.add_attachment(attachment_content, maintype='application', subtype='octet-stream', filename='malware.exe')
    
    with open(eml_path, 'wb') as f:
        f.write(bytes(msg))
        
    parse_email_service(db, email_record.id)
    
    db.refresh(email_record)
    assert email_record.is_parsed == "true"
    assert "Plain body" in email_record.body_text
    assert "HTML body" in email_record.body_html
    
    urls = db.query(URL).filter(URL.email_id == email_record.id).all()
    assert len(urls) == 1
    assert urls[0].url == "https://secure.com"
    
    attachments = db.query(Attachment).filter(Attachment.email_id == email_record.id).all()
    assert len(attachments) == 1
    att = attachments[0]
    assert att.original_filename == "malware.exe"
    assert att.size == len(attachment_content)
    assert att.sha256 == hashlib.sha256(attachment_content).hexdigest()
    
    # Check if file is saved safely
    assert os.path.exists(os.path.join(tmp_path, att.storage_filename))
    assert not att.storage_filename.endswith(".exe") # Generated UUID filename

def test_missing_headers_and_malformed(db, tmp_path):
    job, email_record = _create_mock_job_and_email(db, str(tmp_path))
    eml_path = os.path.join(tmp_path, email_record.storage_filename)
    
    # Write garbage bytes to simulate malformed
    with open(eml_path, 'wb') as f:
        f.write(b"Just some random garbage without proper headers\n\nBody here")
        
    parse_email_service(db, email_record.id)
    
    db.refresh(email_record)
    assert email_record.is_parsed == "true"
    # email module will fallback gracefully
    assert email_record.subject is None
    assert "Body here" in email_record.body_text
