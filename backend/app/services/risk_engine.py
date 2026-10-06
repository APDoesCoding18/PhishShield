import logging
from typing import List
from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.models.risk import RiskResult
from app.schemas.risk import RiskResultSchema

logger = logging.getLogger(__name__)

# MVP Heuristic Weights (Require future calibration)
SEVERITY_WEIGHTS = {
    "informational": 0.0,
    "info": 0.0,
    "low": 1.0,
    "medium": 3.0,
    "high": 6.0,
    "critical": 10.0
}

def map_score_to_severity(score: float) -> str:
    """Maps continuous risk score to categorical severity bucket."""
    if score >= 10.0:
        return "critical"
    elif score >= 6.0:
        return "high"
    elif score >= 3.0:
        return "medium"
    elif score >= 1.0:
        return "low"
    return "informational"

def map_severity_to_verdict(severity: str) -> str:
    """Maps categorical severity to a final actionable verdict."""
    if severity in ("critical", "high"):
        return "malicious"
    elif severity in ("medium", "low"):
        return "suspicious"
    return "clean"

class RiskEngine:
    """
    Consumes normalized Finding objects to produce a deterministic, explainable risk score.
    Does not depend on internal analyzer implementations.
    """
    
    def analyze(self, db: Session, job_id: str, findings: List[Finding]) -> RiskResultSchema:
        """
        Analyzes findings, computes score, generates rationale, and persists RiskResult.
        """
        # 1. Check for Analyzer Failures
        # If there are NO findings, we need to know if it's because it was clean, or if analyzers failed entirely.
        # But this engine just scores findings. We assume the orchestrator will handle job status.
        # If we get here and there are no findings, it's a 0 score.
        
        total_score = 0.0
        contributing_ids = []
        
        # Sort findings by severity weight to extract top contributors for rationale
        scored_findings = []
        
        for f in findings:
            weight = SEVERITY_WEIGHTS.get(f.severity.lower(), 0.0)
            if weight > 0:
                total_score += weight
                contributing_ids.append(f.id)
                scored_findings.append((weight, f))
                
        # Cap score at 100 for normalization, or leave unbounded. We leave it bounded for now.
        if total_score > 100.0:
            total_score = 100.0
            
        severity = map_score_to_severity(total_score)
        verdict = map_severity_to_verdict(severity)
        
        # 2. Generate Explainable Rationale
        if total_score == 0.0:
            rationale = "No suspicious indicators were detected across all analysis modules."
        else:
            # Sort descending by weight
            scored_findings.sort(key=lambda x: x[0], reverse=True)
            top_findings = scored_findings[:3] # Top 3 contributors
            
            reasons = [f"{f.title} ({f.severity})" for _, f in top_findings]
            rationale = f"Email is classified as {verdict.upper()} (Score: {total_score}). Primary indicators: " + ", ".join(reasons) + "."
            if len(scored_findings) > 3:
                rationale += f" (+ {len(scored_findings) - 3} other findings)."
                
        # 3. Persist RiskResult
        try:
            # Check if exists (idempotency)
            existing_result = db.query(RiskResult).filter(RiskResult.job_id == job_id).first()
            if existing_result:
                db.delete(existing_result)
                db.commit()
                
            risk_record = RiskResult(
                job_id=job_id,
                score=total_score,
                severity=severity,
                verdict=verdict,
                rationale=rationale
            )
            db.add(risk_record)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to persist RiskResult for job {job_id}: {e}")
            db.rollback()
            # Still return the schema even if DB fails for resilience
            
        return RiskResultSchema(
            score=total_score,
            severity=severity,
            verdict=verdict,
            rationale=rationale,
            contributing_finding_ids=contributing_ids
        )
