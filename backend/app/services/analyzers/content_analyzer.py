import re
from typing import List, Dict, Any, Tuple
from app.schemas.analyzer import AnalysisContext, AnalysisResult, FindingSchema

class ContentAnalyzer:
    """
    Analyzes the email subject and body text for rule-based phishing indicators.
    Detects urgency, credential requests, financial pressure, etc.
    Does NOT use ML, transformers, or external intelligence.
    """
    
    NAME = "ContentAnalyzer"
    VERSION = "1.0.0"
    
    # Pre-compiled regex patterns for modular detection
    PATTERNS = {
        "urgency": re.compile(
            r'\b(urgent|immediately|within 24 hours|action required|final notice|immediate action|overdue)\b', 
            re.IGNORECASE
        ),
        "credential_requests": re.compile(
            r'\b(password|login|sign in|verify your account|update your account|confirm your identity)\b', 
            re.IGNORECASE
        ),
        "financial_pressure": re.compile(
            r'\b(invoice|payment|wire transfer|banking|transaction|suspend your account|billing)\b', 
            re.IGNORECASE
        ),
        "impersonation": re.compile(
            r'\b(it support|help desk|admin|administrator|human resources|payroll)\b', 
            re.IGNORECASE
        )
    }

    def analyze(self, context: AnalysisContext) -> AnalysisResult:
        result = AnalysisResult(
            analyzer_name=self.NAME,
            analyzer_version=self.VERSION,
            status="success"
        )
        
        try:
            email_record = context.email_record
            
            # Combine subject and body text for analysis
            text_to_analyze = ""
            if email_record.subject:
                text_to_analyze += email_record.subject + "\n\n"
            if email_record.body_text:
                text_to_analyze += email_record.body_text
            elif email_record.body_html:
                # If only HTML is present, we do a very basic tag strip for MVP rules
                text_to_analyze += re.sub(r'<[^>]+>', ' ', email_record.body_html)
                
            if not text_to_analyze.strip():
                result.findings.append(self._create_finding(
                    "empty_content",
                    "info",
                    "high",
                    "Empty Email Content",
                    "The email subject and body are completely empty.",
                    {"subject": bool(email_record.subject), "body": False}
                ))
                return result
                
            # Run modular rules
            for category, pattern in self.PATTERNS.items():
                matches = pattern.findall(text_to_analyze)
                if matches:
                    # Deduplicate and limit to top 5
                    unique_matches = list(set([m.lower() for m in matches]))[:5]
                    
                    if category == "urgency":
                        result.findings.append(self._create_finding(
                            "urgency_indicator",
                            "medium",
                            "high",
                            "Urgency or Pressure Indicator",
                            "Email contains language designed to create a sense of urgency.",
                            {"matched_phrases": unique_matches}
                        ))
                    elif category == "credential_requests":
                        result.findings.append(self._create_finding(
                            "credential_request_indicator",
                            "high",
                            "high",
                            "Suspicious Credential Request",
                            "Email asks for login, password, or account verification.",
                            {"matched_phrases": unique_matches}
                        ))
                    elif category == "financial_pressure":
                        result.findings.append(self._create_finding(
                            "financial_indicator",
                            "medium",
                            "medium",
                            "Financial or Payment Focus",
                            "Email discusses invoices, payments, or banking issues.",
                            {"matched_phrases": unique_matches}
                        ))
                    elif category == "impersonation":
                        result.findings.append(self._create_finding(
                            "impersonation_indicator",
                            "medium",
                            "medium",
                            "Potential Authority Impersonation",
                            "Email references IT, Admin, or HR roles commonly impersonated.",
                            {"matched_phrases": unique_matches}
                        ))

            result.metrics["total_findings"] = len(result.findings)
            result.metrics["content_length"] = len(text_to_analyze)

        except Exception as e:
            result.status = "error"
            result.warnings.append(f"Content Analysis failed: {str(e)}")

        return result
        
    def _create_finding(self, type: str, severity: str, confidence: str, title: str, desc: str, evidence: dict = None) -> FindingSchema:
        return FindingSchema(
            source=self.NAME,
            category="content",
            type=type,
            severity=severity,
            confidence=confidence,
            title=title,
            description=desc,
            evidence=evidence
        )
