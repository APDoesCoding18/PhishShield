import os
import email
from email import policy
from email.message import EmailMessage
import hashlib
import re
import uuid
import logging
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.models.analysis import Email, Attachment, URL, JobStatus

logger = logging.getLogger(__name__)

# Basic URL regex for extracting urls from body
URL_REGEX = re.compile(r'(https?://[^\s<>\'"]+)')

class ParsingException(Exception):
    pass

def _extract_urls(text: str, source: str) -> List[dict]:
    if not text:
        return []
    found_urls = URL_REGEX.findall(text)
    # Return unique urls
    return [{"url": u, "source": source} for u in set(found_urls)]

def _save_attachment(part, workspace_path: str) -> dict:
    """Saves attachment to workspace securely, returns metadata"""
    original_filename = part.get_filename()
    if not original_filename:
        original_filename = "unnamed_attachment.bin"
        
    # Generate safe storage name to prevent path traversal
    storage_filename = f"attachment_{uuid.uuid4().hex}"
    storage_path = os.path.join(workspace_path, storage_filename)
    
    payload = part.get_payload(decode=True)
    if payload is None:
        payload = b""
        
    size = len(payload)
    sha256 = hashlib.sha256(payload).hexdigest()
    
    with open(storage_path, "wb") as f:
        f.write(payload)
        
    return {
        "original_filename": original_filename,
        "storage_filename": storage_filename,
        "mime_type": part.get_content_type(),
        "size": size,
        "sha256": sha256
    }

def parse_email_service(db: Session, email_id: str) -> None:
    """
    Parses the email, extracts headers, body, attachments, and URLs.
    Persists data into database. Does not execute or score.
    """
    email_record = db.query(Email).filter(Email.id == email_id).first()
    if not email_record:
        logger.error(f"Email {email_id} not found.")
        return
        
    job = email_record.job
    workspace_path = job.workspace_path
    eml_path = os.path.join(workspace_path, email_record.storage_filename)
    
    if not os.path.exists(eml_path):
        email_record.is_parsed = "error"
        email_record.parsing_error = "File missing from workspace"
        db.commit()
        return

    try:
        with open(eml_path, "rb") as f:
            msg = email.message_from_binary_file(f, policy=policy.default)
            
        # Extract headers
        email_record.sender = msg.get("From")
        email_record.recipient = msg.get("To")
        email_record.cc = msg.get("Cc")
        email_record.reply_to = msg.get("Reply-To")
        email_record.subject = msg.get("Subject")
        email_record.date_header = msg.get("Date")
        email_record.message_id = msg.get("Message-ID")
        
        body_text = ""
        body_html = ""
        extracted_attachments = []
        
        # Traverse email parts
        for part in msg.walk():
            # Skip multipart containers, just parse the leaves
            if part.is_multipart():
                continue
                
            content_disposition = str(part.get("Content-Disposition", "")).lower()
            content_type = part.get_content_type()
            
            is_attachment = "attachment" in content_disposition or part.get_filename() is not None
            
            if is_attachment:
                # Save securely
                att_meta = _save_attachment(part, workspace_path)
                extracted_attachments.append(att_meta)
            else:
                # Body content
                payload = part.get_payload(decode=True)
                if payload:
                    try:
                        decoded_payload = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
                        if content_type == "text/plain":
                            body_text += decoded_payload + "\n"
                        elif content_type == "text/html":
                            body_html += decoded_payload + "\n"
                    except Exception as e:
                        logger.warning(f"Failed to decode payload in email {email_id}: {e}")

        email_record.body_text = body_text.strip() if body_text else None
        email_record.body_html = body_html.strip() if body_html else None
        
        # Extract URLs
        all_urls = []
        all_urls.extend(_extract_urls(email_record.body_text, "body_text"))
        all_urls.extend(_extract_urls(email_record.body_html, "body_html"))
        
        # Persist Attachments
        for att in extracted_attachments:
            db_att = Attachment(
                email_id=email_record.id,
                original_filename=att["original_filename"],
                storage_filename=att["storage_filename"],
                mime_type=att["mime_type"],
                size=att["size"],
                sha256=att["sha256"]
            )
            db.add(db_att)
            
        # Persist URLs
        # Deduplicate URLs across both sources by keeping the first source found
        url_seen = set()
        for u in all_urls:
            url_str = u["url"]
            if len(url_str) > 2000:  # Bound length
                continue
            if url_str not in url_seen:
                url_seen.add(url_str)
                db_url = URL(
                    email_id=email_record.id,
                    url=url_str,
                    source=u["source"]
                )
                db.add(db_url)
                
        email_record.is_parsed = "true"
        db.commit()

    except Exception as e:
        logger.error(f"Error parsing email {email_id}: {e}")
        db.rollback()
        email_record.is_parsed = "error"
        email_record.parsing_error = str(e)
        db.commit()
