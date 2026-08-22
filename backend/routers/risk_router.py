from fastapi import APIRouter
from schemas.risk_schema import RiskScoreRequest, RiskScoreResponse
from services.risk_service import compute_risk_score

router = APIRouter(prefix="/api/v1/risk", tags=["Risk Scorer"])

@router.post("/score", response_model=RiskScoreResponse)
async def score_risk(payload: RiskScoreRequest):
    return compute_risk_score(payload)