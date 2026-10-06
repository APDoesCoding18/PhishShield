import re
import ipaddress
import urllib.parse
from typing import List, Dict, Any

from app.schemas.analyzer import AnalysisContext, AnalysisResult, FindingSchema
from app.models.analysis import URL

# A basic list of common URL shorteners for the 50% MVP
URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd", 
    "buff.ly", "adf.ly", "bit.do", "mcaf.ee", "su.pr"
}

class UrlAnalyzer:
    """
    Analyzes URLs extracted from emails for basic structural risk indicators.
    Does NOT make external network requests.
    """
    
    NAME = "UrlAnalyzer"
    VERSION = "1.0.0"

    def analyze(self, context: AnalysisContext) -> AnalysisResult:
        result = AnalysisResult(
            analyzer_name=self.NAME,
            analyzer_version=self.VERSION,
            status="success"
        )
        
        try:
            urls = context.db.query(URL).filter(URL.email_id == context.email_record.id).all()
            if not urls:
                result.metrics["total_urls"] = 0
                return result
                
            for db_url in urls:
                self._analyze_url(db_url, result)
                
            context.db.commit()
            result.metrics["total_urls"] = len(urls)
            result.metrics["total_findings"] = len(result.findings)
            
        except Exception as e:
            result.status = "error"
            result.warnings.append(f"URL analysis failed: {str(e)}")
            context.db.rollback()

        return result

    def _analyze_url(self, db_url: URL, result: AnalysisResult) -> None:
        raw_url = db_url.url
        try:
            # Parse URL safely
            parsed = urllib.parse.urlparse(raw_url)
            
            # Normalize URL
            db_url.scheme = parsed.scheme.lower() if parsed.scheme else None
            db_url.domain = parsed.hostname.lower() if parsed.hostname else None
            db_url.port = parsed.port
            
            # Reconstruct normalized URL (strip fragments, etc., for tracking)
            # Safe reconstruction
            db_url.normalized_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                parsed.query,
                ""  # Strip fragment
            ))
            
            domain = db_url.domain or ""
            
            # Check IP address
            is_ip = False
            try:
                # This handles IPv4 and IPv6
                ipaddress.ip_address(domain)
                is_ip = True
            except ValueError:
                pass
                
            db_url.is_ip = is_ip

            # 1. IP-based URL
            if is_ip:
                result.findings.append(self._create_finding(
                    "ip_url", "high", "high", "IP-based URL", 
                    "URL uses a direct IP address instead of a domain name.", raw_url
                ))
            
            # 2. Suspicious Scheme
            if db_url.scheme and db_url.scheme not in ("http", "https"):
                result.findings.append(self._create_finding(
                    "suspicious_scheme", "medium", "high", "Suspicious URL Scheme", 
                    f"URL uses an unusual scheme: {db_url.scheme}", raw_url
                ))
                
            # 3. URL Shortener
            if domain in URL_SHORTENERS:
                result.findings.append(self._create_finding(
                    "url_shortener", "medium", "high", "URL Shortener Detected", 
                    f"URL uses a known shortener service: {domain}", raw_url
                ))
                
            # 4. Unusual Port
            if db_url.port and db_url.port not in (80, 443):
                result.findings.append(self._create_finding(
                    "unusual_port", "medium", "high", "Unusual Port", 
                    f"URL uses a non-standard web port: {db_url.port}", raw_url
                ))
                
            # 5. Suspicious Userinfo (e.g. login credentials in URL)
            if parsed.username or parsed.password:
                result.findings.append(self._create_finding(
                    "suspicious_userinfo", "high", "high", "Suspicious Userinfo", 
                    "URL contains embedded credentials or userinfo, often used for obfuscation.", raw_url
                ))
                
            # 6. Excessive Subdomains
            # Count dots in domain, ignoring known TLD dots
            # Very basic heuristic: more than 3 dots (e.g. a.b.c.d.com) is suspicious
            if domain and not is_ip:
                parts = domain.split('.')
                if len(parts) > 4:
                    result.findings.append(self._create_finding(
                        "excessive_subdomains", "low", "medium", "Excessive Subdomains", 
                        f"Domain {domain} has an unusually high number of subdomains.", raw_url
                    ))

            # 7. Excessive / Suspicious Encoding
            encoded_chars = raw_url.count('%')
            if encoded_chars > 10:
                result.findings.append(self._create_finding(
                    "excessive_encoding", "medium", "high", "Excessive URL Encoding", 
                    f"URL contains {encoded_chars} URL-encoded characters.", raw_url
                ))
                
            # Suspicious bytes like %00, %0a, %0d
            if re.search(r'%00|%0a|%0d', raw_url, re.IGNORECASE):
                result.findings.append(self._create_finding(
                    "suspicious_encoding", "high", "high", "Suspicious Encoded Characters", 
                    "URL contains encoded null bytes, carriage returns, or line feeds.", raw_url
                ))

        except Exception as e:
            # Malformed URL parsing errors
            result.findings.append(self._create_finding(
                "malformed_url", "medium", "high", "Malformed URL", 
                f"Failed to parse URL structurally: {str(e)}", raw_url
            ))
            
    def _create_finding(self, type: str, severity: str, confidence: str, title: str, desc: str, raw_url: str) -> FindingSchema:
        return FindingSchema(
            source=self.NAME,
            category="url_analysis",
            type=type,
            severity=severity,
            confidence=confidence,
            title=title,
            description=desc,
            evidence={"url": raw_url}
        )
