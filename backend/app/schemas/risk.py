from pydantic import BaseModel
from typing import List

class RiskResultSchema(BaseModel):
    score: float
    severity: str
    verdict: str
    rationale: str
    contributing_finding_ids: List[str]
