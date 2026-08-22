from fastapi import APIRouter
from schemas.risk_schema import RiskAnalysisRequest, RiskAnalysisResponse
from services.risk_service import calculate_patent_risk

router = APIRouter(prefix="/api/v1/risk", tags=["Risk Scorer"])

@router.post("/score", response_model=RiskAnalysisResponse)
async def score_patent_risk(payload: RiskAnalysisRequest):
    return calculate_patent_risk(payload)