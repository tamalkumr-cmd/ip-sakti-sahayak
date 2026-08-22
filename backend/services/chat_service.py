"""
Multi-turn consultation logic.

Returns a plain dict (not a Pydantic model) because chat_router.py accesses
the result with dict-style subscripting (result["reply"], result.get(...))
before translating fields — a Pydantic BaseModel instance isn't subscriptable
and would raise TypeError there.

Translation is intentionally NOT done here — chat_router.py already handles
inbound/outbound translation around this function. This function always
works in English.

Key behavior fix vs. the earlier draft: a clarification answer on turn 2+
is now merged with the ORIGINAL question from turn 1 before hitting the
cache/RAG layer. Previously a follow-up answer like "raw herbal extract"
was looked up on its own, losing the original topic entirely.
"""

import copy
from typing import Any, Dict, List, Optional

from schemas.chat_schema import ChatMessage
from services.ai_bridge import execute_rag
from services.cache_service import check_cache

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

_DEFAULT_FOLLOWUPS = [
    "Download compliance dossier PDF",
    "Ask a follow-up question",
    "View related citations",
]


def process_chat_turn(
    session_id: str,
    message: str,
    history: Optional[List[ChatMessage]] = None,
) -> Dict[str, Any]:
    history = history or []
    msg_lower = message.lower()
    is_first_turn = len(history) == 0

    # --- 1. First-turn clarification branch -----------------------------
    if is_first_turn:
        for keyword, trigger in CLARIFICATION_TRIGGERS.items():
            already_answered = any(term in msg_lower for term in _SKIP_TERMS)
            if keyword in msg_lower and not already_answered:
                return {
                    "session_id": session_id,
                    "reply": (
                        "To evaluate your patentability accurately under the Indian Patent Act 1970:\n\n"
                        f"{trigger['question']}"
                    ),
                    "requires_clarification": True,
                    "suggested_followups": list(trigger["followups"]),
                    "verdict": "Clarification Required Before Formal Assessment",
                    "citations": [],
                }

    # --- 2. Build a context-aware query for cache/RAG lookup -------------
    # Merges the ORIGINAL first question with the latest message so a
    # clarification answer doesn't lose the subject it was answering about.
    effective_query = _build_effective_query(message, history)

    # --- 3. Cache lookup ---------------------------------------------------
    cached = check_cache(effective_query)
    if cached is not None:
        return _build_reply(session_id, copy.deepcopy(cached))

    # --- 4. RAG fallback -----------------------------------------------------
    rag_result = execute_rag(query=effective_query, regime_filter="all")
    return _build_reply(session_id, rag_result)


def _build_effective_query(message: str, history: List[ChatMessage]) -> str:
    user_turns = [h.content for h in history if h.role == "user"]
    if not user_turns:
        return message
    original_question = user_turns[0]
    return f"{original_question}. Follow-up detail: {message}"


def _build_reply(session_id: str, result: Dict[str, Any]) -> Dict[str, Any]:
    reply = (
        f"**Verdict:** {result['verdict']}\n\n"
        f"{result['detailed_analysis']}\n\n"
        f"**National Compliance:** {result['national_compliance']}\n\n"
        f"**International Compliance:** {result['international_compliance']}"
    )
    return {
        "session_id": session_id,
        "reply": reply,
        "requires_clarification": False,
        "suggested_followups": list(_DEFAULT_FOLLOWUPS),
        "verdict": result["verdict"],
        "citations": result.get("citations", []),
    }