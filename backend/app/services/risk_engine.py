import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session

from app.models.finding import Finding
from app.models.risk import RiskResult
from app.schemas.risk import RiskResultSchema

logger = logging.getLogger(__name__)

# Base severity weights (representing max single-instance base impact)
SEVERITY_WEIGHTS = {
    "informational": 0.0,
    "info": 0.0,
    "low": 1.0,
    "medium": 3.0,
    "high": 6.0,
    "critical": 10.0
}

# Confidence multipliers
CONFIDENCE_MULTIPLIERS = {
    "high": 1.0,
    "medium": 0.75,
    "low": 0.5,
    "unknown": 0.5
}

# Group caps preventing repeated weak indicators from unbounded inflation
GROUP_CAPS = {
    "informational": 0.0,
    "low": 2.5,       # E.g. max 2.5 pts even with dozens of low findings
    "medium": 6.0,    # E.g. max 6.0 pts even with 25+ excessive encoding or urgency indicators
    "high": 12.0,     # Max 12.0 pts for high category
    "critical": 20.0   # Max 20.0 pts for critical category
}

# Explicit Malicious Indicators: reliable signatures of weaponized content or active attack
MALICIOUS_FINDING_TYPES = {
    "executable_attachment",
    "double_extension",
    "suspicious_userinfo",
    "suspicious_encoding",
}

# High-risk phishing / weaponization combinations
SUSPICIOUS_STRONG_TYPES = {
    "credential_request_indicator",
    "impersonation_indicator",
    "dmarc_fail",
    "spf_fail",
    "ip_url",
    "url_shortener",
    "archive_attachment",
    "suspicious_filename"
}

def derive_group_key(finding: Finding) -> str:
    """
    Groups findings by root-cause / behavioral threat vector rather than arbitrary flat accumulation.
    All instances of repeated behaviors (e.g. 25 URLs with excessive encoding) group together.
    """
    cat = (finding.category or "generic").lower()
    ftype = (finding.finding_type or "unknown").lower()
    return f"{cat}:{ftype}"

def map_score_to_severity(score: float) -> str:
    """Maps continuous risk score (0-100) to categorical severity bucket."""
    if score >= 20.0:
        return "critical"
    elif score >= 12.0:
        return "high"
    elif score >= 5.0:
        return "medium"
    elif score >= 1.0:
        return "low"
    return "informational"

def evaluate_verdict(
    score: float, 
    groups: Dict[str, List[Finding]], 
    has_analyzer_failures: bool = False
) -> Tuple[str, str]:
    """
    Separates verdict generation from raw score accumulation.
    Verdict is determined by evidence quality and threat semantics, not score alone.
    Categories: 'clean', 'suspicious', 'malicious', 'inconclusive'
    """
    if has_analyzer_failures and score == 0.0:
        return "inconclusive", "Analysis encountered critical errors before completing all modules."

    # Check for direct Malicious triggers (e.g. executable attachment, weaponized payload, active attack)
    all_types = set()
    for g_findings in groups.values():
        for f in g_findings:
            all_types.add((f.finding_type or "").lower())

    malicious_matches = all_types.intersection(MALICIOUS_FINDING_TYPES)
    if malicious_matches:
        reasons = ", ".join(sorted(malicious_matches))
        return "malicious", f"Direct weaponized or malicious artifact detected ({reasons})."

    # Multi-vector corroboration:
    # A true phishing attempt combines intent (credential theft/impersonation) with deceit (auth fail or suspicious URL)
    has_credential_or_impersonation = bool({"credential_request_indicator", "impersonation_indicator"}.intersection(all_types))
    has_deceitful_vector = bool({"dmarc_fail", "spf_fail", "ip_url", "url_shortener", "mime_mismatch", "suspicious_filename"}.intersection(all_types))

    if has_credential_or_impersonation and has_deceitful_vector:
        return "malicious", "Corroborated phishing attack: credential harvesting/impersonation combined with deceptive transport or identity vectors."

    # If score is very high (>= 20) with multiple distinct independent high/critical groups
    high_cred_groups = [
        k for k, f_list in groups.items() 
        if any(f.severity.lower() in ("high", "critical") for f in f_list)
    ]
    if score >= 20.0 and len(high_cred_groups) >= 2:
        return "malicious", f"Multi-vector threat corroborated across {len(high_cred_groups)} distinct high-severity groups."

    # Suspicious vs Clean
    if score >= 1.0 or any(f.severity.lower() in ("low", "medium", "high") for f_list in groups.values() for f in f_list):
        return "suspicious", "Indicators detected warranting caution, but evidence does not establish definitive malicious intent."

    return "clean", "No suspicious or malicious indicators were identified across all analysis passes."


class RiskEngine:
    """
    Bounded, group-aware risk engine:
    1. Preserves every original finding for forensic inspection.
    2. Groups findings by root cause to prevent repetitive weak signals from runaway inflation.
    3. Calculates base score with diminishing returns for corroborating instances within each group.
    4. Evaluates threat verdict via explicit evidence policy rather than score threshold alone.
    """

    def analyze(self, db: Session, job_id: str, findings: List[Finding]) -> RiskResultSchema:
        if not findings:
            verdict = "clean"
            severity = "informational"
            score = 0.0
            rationale = "No suspicious indicators were detected across all analysis modules."
            contributing_ids = []
            self._persist_result(db, job_id, score, severity, verdict, rationale)
            return RiskResultSchema(
                score=score,
                severity=severity,
                verdict=verdict,
                rationale=rationale,
                contributing_finding_ids=contributing_ids
            )

        # 1. Group findings by root cause (preserving all original findings)
        groups: Dict[str, List[Finding]] = {}
        contributing_ids: List[str] = []
        for f in findings:
            if f.severity.lower() in ("info", "informational"):
                continue  # Informational signals preserved in DB/report, 0 risk weight
            g_key = derive_group_key(f)
            groups.setdefault(g_key, []).append(f)
            contributing_ids.append(f.id)

        # 2. Bounded Group-Aware Scoring
        # Group Contribution = Base (strongest finding adjusted by confidence) + Diminishing Returns for repeats
        total_score = 0.0
        group_summaries = []

        for g_key, g_findings in groups.items():
            # Find strongest finding in group
            best_weight = 0.0
            best_sev = "low"
            for f in g_findings:
                sev = f.severity.lower()
                conf = (f.confidence or "medium").lower()
                conf_mult = CONFIDENCE_MULTIPLIERS.get(conf, 0.75)
                base_w = SEVERITY_WEIGHTS.get(sev, 0.0) * conf_mult
                if base_w > best_weight:
                    best_weight = base_w
                    best_sev = sev

            # Diminishing returns for additional occurrences in the same group:
            # Each subsequent finding adds only 10% of base weight
            repeat_count = len(g_findings) - 1
            corroboration_bonus = repeat_count * (best_weight * 0.10)

            group_score = best_weight + corroboration_bonus
            # Enforce group ceiling
            cap = GROUP_CAPS.get(best_sev, 6.0)
            group_score = min(group_score, cap)

            total_score += group_score
            group_title = g_findings[0].title
            count_label = f" ({len(g_findings)}x)" if len(g_findings) > 1 else ""
            group_summaries.append((group_score, f"{group_title}{count_label} [{best_sev}]"))

        # Bound overall score to 0.0 - 100.0
        total_score = round(min(100.0, max(0.0, total_score)), 1)
        severity = map_score_to_severity(total_score)

        # 3. Separate Verdict Evaluation
        verdict, verdict_explanation = evaluate_verdict(total_score, groups)

        # 4. Generate Explainable Rationale
        if total_score == 0.0:
            rationale = "No suspicious indicators were detected across all analysis modules."
        else:
            group_summaries.sort(key=lambda x: x[0], reverse=True)
            top_groups = [desc for _, desc in group_summaries[:3]]
            rationale = f"Email classified as {verdict.upper()} (Score: {total_score}). Primary threat factors: {', '.join(top_groups)}."
            if len(group_summaries) > 3:
                rationale += f" (+ {len(group_summaries) - 3} other factor groups)."
            rationale += f" Assessment notes: {verdict_explanation}"

        # 5. Persist RiskResult
        self._persist_result(db, job_id, total_score, severity, verdict, rationale)

        return RiskResultSchema(
            score=total_score,
            severity=severity,
            verdict=verdict,
            rationale=rationale,
            contributing_finding_ids=contributing_ids
        )

    def _persist_result(
        self, 
        db: Session, 
        job_id: str, 
        score: float, 
        severity: str, 
        verdict: str, 
        rationale: str
    ) -> None:
        try:
            existing = db.query(RiskResult).filter(RiskResult.job_id == job_id).first()
            if existing:
                existing.score = score
                existing.severity = severity
                existing.verdict = verdict
                existing.rationale = rationale
            else:
                record = RiskResult(
                    job_id=job_id,
                    score=score,
                    severity=severity,
                    verdict=verdict,
                    rationale=rationale
                )
                db.add(record)
            db.commit()
        except Exception as e:
            logger.error(f"Failed to persist RiskResult for job {job_id}: {e}")
            db.rollback()
