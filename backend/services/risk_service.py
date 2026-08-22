"""
Patent invalidation risk scorer.

Rule-based heuristic (not ML/RAG) -- deliberately simple and explainable,
matching the kind of "why" a judge would want to see in a live demo. Each
rule maps a request field to a risk category, a 0-100 score, and a concrete
remedy action.
"""

from typing import Dict, List

from schemas.risk_schema import RiskBreakdownItem, RiskScoreRequest, RiskScoreResponse


def _traditional_knowledge_risk(payload: RiskScoreRequest) -> RiskBreakdownItem:
    if payload.is_novel_delivery_system:
        return RiskBreakdownItem(
            category="Traditional Knowledge (Section 3(p))",
            risk_level="Low",
            score_percentage=25,
            grounds=(
                "The inclusion of a novel delivery system (e.g. nano-emulsion, liposomal "
                "carrier) overcomes the Section 3(p) classical-knowledge threshold, since the "
                "claim is not merely the raw traditional formulation."
            ),
            remedy_action=(
                "File in-vitro cellular uptake and pharmacokinetic data comparing the raw "
                "extract against the novel formulation to substantiate the technical advance."
            ),
        )
    return RiskBreakdownItem(
        category="Traditional Knowledge (Section 3(p))",
        risk_level="High",
        score_percentage=80,
        grounds=(
            "No novel delivery mechanism is claimed. A formulation using only the raw or "
            "traditionally known form of the botanical ingredient(s) is likely to be treated "
            "as an aggregation of known traditional-knowledge properties under Section 3(p)."
        ),
        remedy_action=(
            "Develop and document a genuine technical modification (delivery system, "
            "synergistic combination with proven enhanced efficacy, novel extraction "
            "process) before filing, or reframe the claim around a demonstrable improvement."
        ),
    )


def _biodiversity_compliance_risk(payload: RiskScoreRequest) -> RiskBreakdownItem:
    if payload.bioresource_sourced_in_india:
        return RiskBreakdownItem(
            category="Biological Diversity Compliance (NBA Form 1)",
            risk_level="High",
            score_percentage=85,
            grounds=(
                "Bioresources sourced within India mandate prior approval under Section 6 of "
                "the Biological Diversity Act, 2002 before an IP application can be filed. "
                "Failure to obtain this clearance is an independent ground for invalidation, "
                "separate from the patentability analysis itself."
            ),
            remedy_action=(
                "Submit Form 1 application to the National Biodiversity Authority (NBA), "
                "Chennai, and obtain approval before filing or proceeding to grant."
            ),
        )
    return RiskBreakdownItem(
        category="Biological Diversity Compliance (NBA Form 1)",
        risk_level="Low",
        score_percentage=20,
        grounds=(
            "Bioresources are not sourced from India, so Section 6 of the Biological "
            "Diversity Act, 2002 does not apply to this application."
        ),
        remedy_action=(
            "Retain sourcing documentation (certificates of origin, supplier records) in "
            "case provenance is challenged during opposition proceedings."
        ),
    )


def _therapeutic_claim_risk(payload: RiskScoreRequest) -> RiskBreakdownItem:
    claim_count = len(payload.therapeutic_claims)
    if claim_count == 0:
        return RiskBreakdownItem(
            category="Therapeutic Claim Substantiation",
            risk_level="Low",
            score_percentage=10,
            grounds="No specific therapeutic claims are made, so there is minimal exposure to an unsubstantiated-efficacy challenge.",
            remedy_action="If therapeutic claims are added later, ensure each is backed by clinical or pharmacokinetic data before filing.",
        )
    return RiskBreakdownItem(
        category="Therapeutic Claim Substantiation",
        risk_level="Moderate",
        score_percentage=50,
        grounds=(
            f"{claim_count} therapeutic claim(s) are asserted ({', '.join(payload.therapeutic_claims)}). "
            "Each claim of enhanced efficacy must be independently substantiated to withstand "
            "opposition on grounds of insufficient disclosure or lack of proven therapeutic efficacy."
        ),
        remedy_action=(
            "Compile clinical, pharmacokinetic, or in-vitro evidence for each individual "
            "therapeutic claim listed, rather than relying on a single general efficacy dataset."
        ),
    )


def _overall_risk_label(score: int) -> str:
    if score < 34:
        return "Low"
    if score < 67:
        return "Moderate"
    return "High"


def _eligibility_verdict(payload: RiskScoreRequest) -> str:
    parts: List[str] = []
    if payload.is_novel_delivery_system:
        parts.append("Patentable with Section 3(d) Bioavailability Filing")
    else:
        parts.append("Likely Non-Patentable under Section 3(p) Absent Technical Modification")
    if payload.bioresource_sourced_in_india:
        parts.append("Form 1 NBA Compliance Required")
    return " & ".join(parts)


def compute_risk_score(payload: RiskScoreRequest) -> RiskScoreResponse:
    breakdown = [
        _traditional_knowledge_risk(payload),
        _biodiversity_compliance_risk(payload),
        _therapeutic_claim_risk(payload),
    ]
    composite = round(sum(item.score_percentage for item in breakdown) / len(breakdown))

    return RiskScoreResponse(
        status="success",
        overall_invalidation_risk=_overall_risk_label(composite),
        composite_risk_score=composite,
        breakdown=breakdown,
        patent_eligibility_verdict=_eligibility_verdict(payload),
    )