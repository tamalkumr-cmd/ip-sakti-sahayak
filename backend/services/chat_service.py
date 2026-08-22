import uuid
from typing import Dict, Any, List
from schemas.chat_schema import ChatMessage
from services.cache_service import check_cache
from services.ai_bridge import execute_rag

# Rule heuristics to detect ambiguous Ayush queries needing follow-up
CLARIFICATION_TRIGGERS = {
    "turmeric": {
        "missing_aspect": "delivery mechanism",
        "question": "Is this formulation using raw turmeric extract, or have you developed an enhanced delivery carrier (such as nano-curcumin or liposomal encapsulation)?",
        "followups": [
            "It uses a novel nano-carrier system",
            "It is a traditional herbal paste/extract",
            "We have bio-availability enhancement data"
        ]
    },
    "neem": {
        "missing_aspect": "source of biological material",
        "question": "Will the Neem resources be sourced domestically within India? (This determines whether NBA Form-1 approval is mandatory under Section 3 of the BD Act 2002).",
        "followups": [
            "Sourced from domestic Indian farmers",
            "Imported raw material from abroad",
            "Cultivated on private commercial facility"
        ]
    }
}

def process_chat_turn(session_id: str, message: str, history: List[ChatMessage]) -> Dict[str, Any]:
    msg_lower = message.lower()

    # 1. Check if the user query triggers a regulatory clarification branch
    if len(history) == 0:
        for keyword, trigger_data in CLARIFICATION_TRIGGERS.items():
            if keyword in msg_lower and not any(term in msg_lower for term in ["nano", "liposome", "extract", "nba", "form 1"]):
                return {
                    "session_id": session_id or str(uuid.uuid4()),
                    "reply": f"To evaluate your patentability accurately under the Indian Patent Act 1970:\n\n{trigger_data['question']}",
                    "requires_clarification": True,
                    "suggested_followups": trigger_data["followups"],
                    "verdict": "Clarification Required Before Formal Assessment",
                    "citations": []
                }

    # 2. Check pre-computed cache
    cached = check_cache(message)
    if cached:
        return {
            "session_id": session_id or str(uuid.uuid4()),
            "reply": f"**Verdict:** {cached['verdict']}\n\n{cached['detailed_analysis']}\n\n**National Compliance:** {cached['national_compliance']}",
            "requires_clarification": False,
            "suggested_followups": [
                "Download compliance dossier PDF",
                "Check US FDA 21 CFR dietary rules",
                "View NBA Form 1 filing steps"
            ],
            "verdict": cached["verdict"],
            "citations": cached.get("citations", [])
        }

    # 3. Process via RAG pipeline
    rag_res = execute_rag(message)
    return {
        "session_id": session_id or str(uuid.uuid4()),
        "reply": f"**Verdict:** {rag_res['verdict']}\n\n{rag_res['detailed_analysis']}",
        "requires_clarification": False,
        "suggested_followups": ["Export compliance report", "Inspect cited legal gazettes"],
        "verdict": rag_res.get("verdict", "Evaluated"),
        "citations": rag_res.get("citations", [])
    }