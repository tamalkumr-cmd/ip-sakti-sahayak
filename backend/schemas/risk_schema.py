from pydantic import BaseModel
from typing import List, Dict

class RiskAnalysisRequest(BaseModel):
    formulation_name: str
    botanical_ingredients: List[str]
    is_novel_delivery_system: bool = False
    therapeutic_claims: List[str]
    bioresource_sourced_in_india: bool = True

class RiskFactor(BaseModel):
    category: str
    risk_level: str  # "Low", "Medium", "High"
    score_percentage: int
    grounds: str
    remedy_action: str

class RiskAnalysisResponse(BaseModel):
    status: str = "success"
    overall_invalidation_risk: str  # "Low", "Moderate", "High", "Critical"
    composite_risk_score: int       # 0 - 100
    breakdown: List[RiskFactor]
    patent_eligibility_verdict: str