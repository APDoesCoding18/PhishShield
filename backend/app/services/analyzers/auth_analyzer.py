import os
import email
from email import policy
import re
from typing import Dict, Any
from app.schemas.analyzer import AnalysisContext, AnalysisResult, FindingSchema

class AuthenticationAnalyzer:
    """
    Analyzes SPF, DKIM, and DMARC results from the Authentication-Results header.
    Produces standardized findings.
    """
    
    NAME = "AuthenticationAnalyzer"
    VERSION = "1.0.0"
    
    def analyze(self, context: AnalysisContext) -> AnalysisResult:
        result = AnalysisResult(
            analyzer_name=self.NAME,
            analyzer_version=self.VERSION,
            status="success"
        )
        
        eml_path = os.path.join(context.workspace_path, context.email_record.storage_filename)
        if not os.path.exists(eml_path):
            result.status = "error"
            result.warnings.append("Email file not found in workspace")
            return result
            
        try:
            with open(eml_path, "rb") as f:
                msg = email.message_from_binary_file(f, policy=policy.default)
                
            # Authentication-Results can appear multiple times
            auth_headers = msg.get_all("Authentication-Results", [])
            
            if not auth_headers:
                # Missing headers
                result.findings.append(self._create_finding(
                    type="missing_headers",
                    severity="medium",
                    confidence="high",
                    title="Missing Authentication Headers",
                    desc="No Authentication-Results headers found. SPF/DKIM/DMARC status is unknown."
                ))
                return result
                
            # Combine all auth headers into a single string to parse broadly
            # Example: "mx.google.com; dkim=pass header.i=@example.com; spf=pass (google.com: domain of sender@example.com designates 1.2.3.4 as permitted sender)"
            full_auth_text = " ".join(auth_headers).lower()
            
            # Simple regex extractors
            spf_match = re.search(r'spf=(pass|fail|softfail|neutral|none|temperror|permerror)', full_auth_text)
            dkim_match = re.search(r'dkim=(pass|fail|neutral|none|temperror|permerror)', full_auth_text)
            dmarc_match = re.search(r'dmarc=(pass|fail|none|temperror|permerror)', full_auth_text)
            
            raw_evidence = {
                "spf": spf_match.group(1) if spf_match else "unavailable",
                "dkim": dkim_match.group(1) if dkim_match else "unavailable",
                "dmarc": dmarc_match.group(1) if dmarc_match else "unavailable",
                "raw_headers": auth_headers
            }
            
            result.raw_results = raw_evidence
            
            # Evaluate SPF
            spf_val = raw_evidence["spf"]
            if spf_val in ("fail", "softfail"):
                result.findings.append(self._create_finding("spf_fail", "high", "high", "SPF Failed", f"SPF check resulted in {spf_val}", raw_evidence))
            elif spf_val in ("neutral", "none"):
                result.findings.append(self._create_finding("spf_neutral", "medium", "high", "SPF Neutral/None", "Domain has no valid SPF record", raw_evidence))
            elif spf_val == "pass":
                result.findings.append(self._create_finding("spf_pass", "info", "high", "SPF Passed", "SPF check passed", raw_evidence))
                
            # Evaluate DKIM
            dkim_val = raw_evidence["dkim"]
            if dkim_val == "fail":
                result.findings.append(self._create_finding("dkim_fail", "high", "high", "DKIM Failed", "DKIM signature failed validation", raw_evidence))
            elif dkim_val in ("neutral", "none"):
                result.findings.append(self._create_finding("dkim_neutral", "medium", "high", "DKIM Neutral/None", "No valid DKIM signature found", raw_evidence))
            elif dkim_val == "pass":
                result.findings.append(self._create_finding("dkim_pass", "info", "high", "DKIM Passed", "DKIM signature is valid", raw_evidence))
                
            # Evaluate DMARC
            dmarc_val = raw_evidence["dmarc"]
            if dmarc_val == "fail":
                result.findings.append(self._create_finding("dmarc_fail", "high", "high", "DMARC Failed", "DMARC policy validation failed", raw_evidence))
            elif dmarc_val in ("neutral", "none"):
                result.findings.append(self._create_finding("dmarc_neutral", "medium", "high", "DMARC Neutral/None", "No valid DMARC policy found", raw_evidence))
            elif dmarc_val == "pass":
                result.findings.append(self._create_finding("dmarc_pass", "info", "high", "DMARC Passed", "DMARC policy is valid", raw_evidence))

            result.metrics["total_findings"] = len(result.findings)

        except Exception as e:
            result.status = "error"
            result.warnings.append(f"Analysis failed with error: {str(e)}")

        return result
        
    def _create_finding(self, type: str, severity: str, confidence: str, title: str, desc: str, evidence: dict = None) -> FindingSchema:
        return FindingSchema(
            source=self.NAME,
            category="authentication",
            type=type,
            severity=severity,
            confidence=confidence,
            title=title,
            description=desc,
            evidence=evidence
        )
