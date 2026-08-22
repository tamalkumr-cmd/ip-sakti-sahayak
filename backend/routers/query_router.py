import copy

from fastapi import APIRouter
from schemas.query_schema import QueryRequest, QueryResponse
from services.cache_service import check_cache
from services.translation_service import translate_to_english, translate_from_english
from services.ai_bridge import execute_rag

router = APIRouter(prefix="/api/v1", tags=["Query Engine"])

@router.post("/query", response_model=QueryResponse)
async def handle_query(payload: QueryRequest):
    # 1. Translate inbound query to English for vector similarity
    query_in_en = translate_to_english(payload.query, source_lang=payload.language)

    # 2. Check Demo Cache for instant response (<50ms)
    cached = check_cache(query_in_en)
    if cached:
        # FIXED: was cached.copy() — a shallow copy still shares the nested
        # `citations` list/dicts with the module-level DEMO_CACHE. Any future
        # code that mutates a citation in place (e.g. to translate a snippet)
        # would permanently corrupt the shared cache for every later request.
        result = copy.deepcopy(cached)
    else:
        # 3. Call AI RAG Engine
        result = execute_rag(query=query_in_en, regime_filter=payload.regime_filter)

    # 4. If user requested an Indic language, translate free-text fields back.
    # NOTE: verdict is intentionally NOT translated — see chat_router.py for
    # why (frontend badge-matching relies on the exact English string).
    if payload.language != "en":
        result["detailed_analysis"] = translate_from_english(result["detailed_analysis"], target_lang=payload.language)
        result["national_compliance"] = translate_from_english(result["national_compliance"], target_lang=payload.language)
        result["international_compliance"] = translate_from_english(result["international_compliance"], target_lang=payload.language)

    result["query_in_english"] = query_in_en
    return result