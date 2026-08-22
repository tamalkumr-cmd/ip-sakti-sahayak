from typing import Dict, Any
from schemas.risk_schema import RiskAnalysisRequest, RiskAnalysisResponse, RiskFactor

KNOWN_TKDL_HERBS = {
    "ashwagandha": "TKDL Ref: AY/602 - General rejuvenator and adaptogen.",
    "turmeric": "TKDL Ref: AY/104 - Anti-inflammatory and wound healing.",
    "curcumin": "TKDL Ref: AY/104 - Standard extract of Curcuma longa.",
    "neem": "TKDL Ref: UN/883 - Antifungal and antimicrobial use.",
    "triphala": "TKDL Ref: AY/1402 - Digestive and bowel regulatory formulation.",
    "tulsi": "TKDL Ref: AY/912 - Respiratory and immunity booster.",
    "brahmi": "TKDL Ref: AY/301 - Cognitive and memory enhancement."
}

def calculate_patent_risk(payload: RiskAnalysisRequest) -> Dict[str, Any]:
    factors = []
    total_score = 0

    # 1. Evaluate Section 3(p) Risk
    matched_tkdl = [h for h in payload.botanical_ingredients if h.lower() in KNOWN_TKDL_HERBS]
    if matched_tkdl and not payload.is_novel_delivery_system:
        p_score = 90
        p_level = "High"
        p_grounds = f"Direct aggregation of traditionally known bioresources ({', '.join(matched_tkdl)}) with standard extraction."
        p_remedy = "Reformulate using novel nanocarrier or present comparative bioavailability synergy data under Section 3(d)."
    elif matched_tkdl and payload.is_novel_delivery_system:
        p_score = 30
        p_level = "Low"
        p_grounds = "Novel delivery mechanism claimed over traditional herbs."
        p_remedy = "Include clinical pharmacokinetic assay proof in complete specification."
    else:
        p_score = 15
        p_level = "Low"
        p_grounds = "No direct match with canonical single-herb TKDL monographs."
        p_remedy = "Proceed with routine prior-art novelty search."

    factors.append(RiskFactor(
        category="Section 3(p) Traditional Knowledge Exclusion",
        risk_level=p_level,
        score_percentage=p_score,
        grounds=p_grounds,
        remedy_action=p_remedy
    ))
    total_score += p_score

    # 2. Evaluate NBA Section 3 Biological Diversity Act Risk
    if payload.bioresource_sourced_in_india:
        nba_score = 75
        nba_level = "High"
        nba_grounds = "Biological resources sourced from Indian territory require mandatory National Biodiversity Authority clearance."
        nba_remedy = "File NBA Form 1 before commercializing or filing foreign patent counterparts."
    else:
        nba_score = 10
        nba_level = "Low"
        nba_grounds = "Synthesized or non-Indian biological material exempt from NBA Form 1."
        nba_remedy = "Maintain certificate of origin documentation."

    factors.append(RiskFactor(
        category="NBA Biodiversity Compliance (BD Act 2002)",
        risk_level=nba_level,
        score_percentage=nba_score,
        grounds=nba_grounds,
        remedy_action=nba_remedy
    ))
    total_score += nba_score

    composite = int(total_score / 2)
    overall = "High" if composite >= 60 else "Moderate" if composite >= 35 else "Low"
    verdict = (
        "Likely Rejection under Section 3(p) unless delivery mechanism novelty is proven"
        if composite >= 60 else
        "Patentable with Form 1 NBA Compliance & Section 3(d) Bioavailability Filing"
    )

    return {
        "status": "success",
        "overall_invalidation_risk": overall,
        "composite_risk_score": composite,
        "breakdown": factors,
        "patent_eligibility_verdict": verdict
    }