
"""
Multi-turn consultation logic.
 
The key fix here vs. the earlier draft: a clarification answer on turn 2+
is now merged with the ORIGINAL question from turn 1 before hitting the
cache/RAG layer. Previously, a follow-up answer like "raw herbal extract"
was looked up on its own — losing the "turmeric" context from turn 1
entirely, so the assistant would essentially forget what was being asked
about the moment the user answered the clarifying question.
"""
 
from typing import Any, Dict, List, Optional
 
from backend.schemas.chat_schema import ChatMessage, ChatSessionResponse
from backend.schemas.query_schema import QueryResponse
from backend.services.ai_bridge import execute_rag_pipeline
from backend.services.cache_service import get_cached_response
from backend.services.translation_service import translate_text
 
# Terms that, if already present in the FIRST message, mean the user has
# already pre-answered the clarification — so we skip asking it again.
_SKIP_TERMS = ["nano", "liposome", "extract", "nba", "form 1", "form-1"]
 
CLARIFICATION_TRIGGERS = {
    "turmeric": {
        "question": (
            "Is this formulation using raw turmeric extract, or have you developed an "
            "enhanced delivery carrier (such as nano-curcumin or liposomal encapsulation)?"
        ),
        "followups": [
            "It uses a novel nano-carrier system",
            "It is a traditional herbal paste/extract",
            "We have bio-availability enhancement data",
        ],
    },
    "neem": {
        "question": (
            "Will the Neem resources be sourced domestically within India? (This determines "
            "whether NBA Form-1 approval is mandatory under Section 3 of the BD Act 2002.)"
        ),
        "followups": [
            "Sourced from domestic Indian farmers",
            "Imported raw material from abroad",
            "Cultivated on a private commercial facility",
        ],
    },
}
 
_DEFAULT_FOLLOWUPS_EN = [
    "Download compliance dossier PDF",
    "Ask a follow-up question",
    "View related citations",
]
 
 
def process_chat_turn(
    session_id: str,
    message: str,
    history: Optional[List[ChatMessage]] = None,
    language: str = "en",
) -> ChatSessionResponse:
    history = history or []
    msg_lower = message.lower()
    is_first_turn = len(history) == 0
 
    # --- 1. First-turn clarification branch -----------------------------
    if is_first_turn:
        for keyword, trigger in CLARIFICATION_TRIGGERS.items():
            already_answered = any(term in msg_lower for term in _SKIP_TERMS)
            if keyword in msg_lower and not already_answered:
                return _clarification_response(session_id, trigger, language)
 
    # --- 2. Build a context-aware query for cache/RAG lookup -------------
    # Merges the ORIGINAL first question with the latest message so a
    # clarification answer ("raw herbal extract") doesn't lose the subject
    # ("turmeric") it was answering about.
    effective_query = _build_effective_query(message, history)
 
    # --- 3. Cache lookup --------------------------------------------------
    cached = get_cached_response(effective_query)
    if cached is not None:
        return _response_from_query_response(session_id, cached, language)
 
    # --- 4. RAG fallback ---------------------------------------------------
    rag_dict = execute_rag_pipeline(query=effective_query, regime_filter="all")
    rag_response = QueryResponse(**rag_dict)
    return _response_from_query_response(session_id, rag_response, language)
 
 
def _build_effective_query(message: str, history: List[ChatMessage]) -> str:
    user_turns = [h.content for h in history if h.role == "user"]
    if not user_turns:
        return message
    original_question = user_turns[0]
    return f"{original_question}. Follow-up detail: {message}"
 
 
def _clarification_response(session_id: str, trigger: Dict[str, Any], language: str) -> ChatSessionResponse:
    reply_en = (
        "To evaluate your patentability accurately under the Indian Patent Act 1970:\n\n"
        f"{trigger['question']}"
    )
    reply = translate_text(reply_en, source_lang="en", target_lang=language) if language != "en" else reply_en
    followups = (
        [translate_text(f, source_lang="en", target_lang=language) for f in trigger["followups"]]
        if language != "en"
        else trigger["followups"]
    )
    return ChatSessionResponse(
        session_id=session_id,
        reply=reply,
        requires_clarification=True,
        suggested_followups=followups,
        # Not translated deliberately: this is a chat-specific status string,
        # not the locked QueryResponse verdict enum, so it's safe as free text
        # either way — but keeping it in English keeps behavior predictable
        # for any frontend logic that might key off it.
        verdict="Clarification Required Before Formal Assessment",
        citations=[],
    )
 
 
def _response_from_query_response(
    session_id: str, qr: QueryResponse, language: str
) -> ChatSessionResponse:
    reply_en = f"**Verdict:** {qr.verdict}\n\n{qr.legal_rationale}"
    if qr.compliance_checklist:
        bullets = "\n".join(f"- {item}" for item in qr.compliance_checklist)
        reply_en += f"\n\n**Compliance Checklist:**\n{bullets}"
 
    reply = translate_text(reply_en, source_lang="en", target_lang=language) if language != "en" else reply_en
    followups = (
        [translate_text(f, source_lang="en", target_lang=language) for f in _DEFAULT_FOLLOWUPS_EN]
        if language != "en"
        else _DEFAULT_FOLLOWUPS_EN
    )
 
    return ChatSessionResponse(
        session_id=session_id,
        reply=reply,
        requires_clarification=False,
        suggested_followups=followups,
        verdict=qr.verdict,  # untranslated — matches the locked enum, safe for badge logic
        citations=qr.citations,
    )
 
