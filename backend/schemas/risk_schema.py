from typing import List

from pydantic import BaseModel, Field


class RiskScoreRequest(BaseModel):
    formulation_name: str
    botanical_ingredients: List[str]
    is_novel_delivery_system: bool
    therapeutic_claims: List[str]
    bioresource_sourced_in_india: bool


class RiskBreakdownItem(BaseModel):
    category: str
    risk_level: str  # "Low" | "Moderate" | "High"
    score_percentage: int = Field(..., ge=0, le=100)
    grounds: str
    remedy_action: str


class RiskScoreResponse(BaseModel):
    status: str = "success"
    overall_invalidation_risk: str  # "Low" | "Moderate" | "High"
    composite_risk_score: int = Field(..., ge=0, le=100)
    breakdown: List[RiskBreakdownItem]
    patent_eligibility_verdict: str