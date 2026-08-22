from fastapi import APIRouter, Request, HTTPException
from schemas.query_schema import QueryRequest, QueryResponse
from services.translation_service import translate_to_english, translate_from_english
from services.cache_service import check_cache
from services.ai_bridge import execute_rag

router = APIRouter(prefix="/api/v1", tags=["Query Engine"])

NON_AYUSH_KEYWORDS = ["trademark", "logo", "brand name", "software", "crypto", "nft", "copyright", "music", "movie"]

@router.post("/query", response_model=QueryResponse)
async def process_query(payload: QueryRequest, request: Request):
    raw_query = payload.query.strip()
    if not raw_query:
        raise HTTPException(status_code=422, detail="Query cannot be empty.")

    # 1. Base URL Resolution (supports hosted Render URL and localhost)
    base_url = str(request.base_url).rstrip("/")

    # 2. Multilingual translation
    eng_query = translate_to_english(raw_query, source_lang=payload.language)

    # 3. Abstain Logic (Check if out of Ayush / patent scope)
    query_lower = eng_query.lower()
    if any(k in query_lower for k in NON_AYUSH_KEYWORDS):
        analysis = "This query falls outside the scope of Ayush Intellectual Property, Patent Act 1970, and Biological Diversity Act 2002. IP-SAKTI Sahayak evaluates botanical formulations, traditional knowledge patentability (Section 3p/3d), and regulatory compliance."
        if payload.language != "en":
            analysis = translate_from_english(analysis, target_lang=payload.language)
        
        return QueryResponse(
            status="abstained",
            query_in_english=eng_query,
            verdict="Abstained (Out of Scope)",
            confidence=0.10,
            detailed_analysis=analysis,
            national_compliance="N/A — Not an Ayush bio-resource query.",
            international_compliance="N/A",
            citations=[]
        )

    # 4. Check Fast-Cache
    cached_data = check_cache(eng_query, base_url=base_url)
    if cached_data:
        verdict = cached_data["verdict"]
        analysis = cached_data["detailed_analysis"]
        nat_comp = cached_data["national_compliance"]
        int_comp = cached_data["international_compliance"]
        citations = cached_data["citations"]
        confidence = cached_data.get("confidence", 0.95)
    else:
        # 5. RAG execution fallback
        rag_res = execute_rag(eng_query, regime_filter=payload.regime_filter)
        verdict = rag_res.get("verdict", "Conditional Assessment")
        analysis = rag_res.get("detailed_analysis", "Analyzed against statutory regulations.")
        nat_comp = rag_res.get("national_compliance", "Refer to BD Act 2002.")
        int_comp = rag_res.get("international_compliance", "Refer to target pharmacopeia.")
        citations = rag_res.get("citations", [])
        confidence = 0.85

    # 6. Translate outputs back if request language is not English
    if payload.language != "en":
        verdict = translate_from_english(verdict, target_lang=payload.language)
        analysis = translate_from_english(analysis, target_lang=payload.language)
        nat_comp = translate_from_english(nat_comp, target_lang=payload.language)
        int_comp = translate_from_english(int_comp, target_lang=payload.language)

    return QueryResponse(
        status="success",
        query_in_english=eng_query,
        verdict=verdict,
        confidence=confidence,
        detailed_analysis=analysis,
        national_compliance=nat_comp,
        international_compliance=int_comp,
        citations=citations
    )