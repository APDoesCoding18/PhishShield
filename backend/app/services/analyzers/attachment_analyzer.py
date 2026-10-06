import os
import re
from typing import Dict, Any, Tuple

from app.schemas.analyzer import AnalysisContext, AnalysisResult, FindingSchema
from app.models.analysis import Attachment

# Basic magic bytes for MVP signature identification
MAGIC_BYTES = {
    b'MZ': ('application/x-msdownload', 'executable'),
    b'%PDF': ('application/pdf', 'pdf'),
    b'PK\x03\x04': ('application/zip', 'zip'),
    b'\xd0\xcf\x11\xe0': ('application/vnd.ms-office', 'ole2'),
    b'Rar!': ('application/x-rar-compressed', 'rar'),
    b'\x7fELF': ('application/x-elf', 'executable')
}

# Suspicious keywords in filenames
SUSPICIOUS_KEYWORDS = ["invoice", "urgent", "payment", "receipt", "document", "statement", "order"]

class AttachmentAnalyzer:
    """
    Analyzes attachments extracted from emails.
    Performs static structural checks, magic byte validation, and anomaly detection.
    """
    
    NAME = "AttachmentAnalyzer"
    VERSION = "1.0.0"

    def analyze(self, context: AnalysisContext) -> AnalysisResult:
        result = AnalysisResult(
            analyzer_name=self.NAME,
            analyzer_version=self.VERSION,
            status="success"
        )
        
        try:
            attachments = context.db.query(Attachment).filter(Attachment.email_id == context.email_record.id).all()
            if not attachments:
                result.metrics["total_attachments"] = 0
                return result
                
            for db_att in attachments:
                self._analyze_attachment(db_att, context.workspace_path, result)
                
            context.db.commit()
            result.metrics["total_attachments"] = len(attachments)
            result.metrics["total_findings"] = len(result.findings)
            
        except Exception as e:
            result.status = "error"
            result.warnings.append(f"Attachment analysis failed: {str(e)}")
            context.db.rollback()

        return result

    def _get_file_signature(self, filepath: str) -> Tuple[str, str]:
        """Reads the first 4 bytes to guess the MIME type based on magic bytes."""
        try:
            with open(filepath, "rb") as f:
                header = f.read(4)
                
            # Check 4 bytes, then 2 bytes
            for magic, (mime, ftype) in MAGIC_BYTES.items():
                if header.startswith(magic):
                    return mime, ftype
                    
            return "application/octet-stream", "unknown"
        except Exception:
            return "application/octet-stream", "unknown"

    def _analyze_attachment(self, db_att: Attachment, workspace_path: str, result: AnalysisResult) -> None:
        file_path = os.path.join(workspace_path, db_att.storage_filename)
        if not os.path.exists(file_path):
            result.warnings.append(f"Attachment file missing: {db_att.storage_filename}")
            return
            
        original_name = (db_att.original_filename or "").lower()
        
        # 1. Inspect Magic Bytes
        detected_mime, ftype = self._get_file_signature(file_path)
        db_att.detected_mime_type = detected_mime
        
        is_exec = ftype == "executable"
        db_att.is_executable = is_exec
        
        # 2. Extension / MIME Mismatch
        declared_mime = (db_att.mime_type or "").lower()
        # Basic check: if signature says it's a ZIP/PDF/EXE but declared is totally different
        # Ignore octet-stream as a generic fallback mismatch
        if declared_mime and detected_mime != "application/octet-stream":
            if detected_mime not in declared_mime and declared_mime not in detected_mime:
                if not (detected_mime == "application/zip" and "officedocument" in declared_mime):
                    result.findings.append(self._create_finding(
                        "mime_mismatch", "high", "high", "MIME Type Mismatch", 
                        f"Declared MIME ({declared_mime}) does not match detected signature ({detected_mime}).", 
                        db_att.sha256
                    ))

        # 3. Suspicious Executable
        if is_exec:
            result.findings.append(self._create_finding(
                "executable_attachment", "critical", "high", "Executable Attachment", 
                "Attachment contains executable magic bytes (MZ or ELF).", 
                db_att.sha256
            ))
            
        # 4. Double Extension (e.g. document.pdf.exe)
        parts = original_name.split('.')
        if len(parts) >= 3:
            # Check if last part is an extension and second to last is also an extension
            ext1 = parts[-2]
            ext2 = parts[-1]
            known_exts = ["pdf", "doc", "docx", "xls", "xlsx", "txt", "jpg", "png", "zip", "exe", "bat", "js", "vbs", "scr", "rar"]
            if ext1 in known_exts and ext2 in known_exts:
                result.findings.append(self._create_finding(
                    "double_extension", "high", "high", "Double Extension", 
                    f"Filename uses a double extension pattern: .{ext1}.{ext2}", 
                    db_att.sha256
                ))

        # 5. Unusually Large Attachment
        # Let's say > 10MB (10485760 bytes) is suspicious for typical automated email
        if db_att.size > 10485760:
            result.findings.append(self._create_finding(
                "large_attachment", "low", "medium", "Large Attachment", 
                f"Attachment is unusually large: {db_att.size} bytes.", 
                db_att.sha256
            ))

        # 6. Archive Attachment
        if ftype in ("zip", "rar") or original_name.endswith((".zip", ".rar", ".7z", ".tar.gz")):
            result.findings.append(self._create_finding(
                "archive_attachment", "medium", "high", "Archive Attachment", 
                "Attachment is an archive file. May contain hidden payloads.", 
                db_att.sha256
            ))

        # 7. Suspicious Filename Patterns
        if any(kw in original_name for kw in SUSPICIOUS_KEYWORDS):
            # It's highly suspicious if it's an executable/archive pretending to be an invoice
            if is_exec or ftype in ("zip", "rar") or original_name.endswith((".exe", ".scr", ".vbs", ".js")):
                result.findings.append(self._create_finding(
                    "suspicious_filename", "high", "high", "Suspicious Filename Pattern", 
                    f"Filename contains social engineering keywords combined with risky file types: {original_name}", 
                    db_att.sha256
                ))
            
    def _create_finding(self, type: str, severity: str, confidence: str, title: str, desc: str, sha256: str) -> FindingSchema:
        return FindingSchema(
            source=self.NAME,
            category="attachment_analysis",
            type=type,
            severity=severity,
            confidence=confidence,
            title=title,
            description=desc,
            evidence={"sha256": sha256}
        )
