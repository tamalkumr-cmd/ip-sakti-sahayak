from fastapi import APIRouter, Request
from schemas.chat_schema import ChatSessionRequest, ChatSessionResponse
from services.chat_service import process_chat_turn
from services.translation_service import translate_to_english, translate_from_english

router = APIRouter(prefix="/api/v1/chat", tags=["Multi-Turn Consultation"])

@router.post("/message", response_model=ChatSessionResponse)
async def handle_chat_message(payload: ChatSessionRequest, request: Request):
    # Resolve current host base URL
    base_url = str(request.base_url).rstrip("/")

    # Translate inbound message to English
    eng_message = translate_to_english(payload.message, source_lang=payload.language)
    
    # Process turn with conversation history context
    result = process_chat_turn(
        session_id=payload.session_id,
        message=eng_message,
        history=payload.history or []
    )

    # Dynamically patch citation PDF URLs to match current host
    if result.get("citations"):
        for citation in result["citations"]:
            doc_id = citation.get("doc_id", "")
            page = citation.get("page_number", 1)
            citation["pdf_url"] = f"{base_url}/api/v1/docs/{doc_id}.pdf#page={page}"
    
    # Translate outbound reply back if necessary
    if payload.language != "en":
        result["reply"] = translate_from_english(result["reply"], target_lang=payload.language)
        if result.get("verdict"):
            result["verdict"] = translate_from_english(result["verdict"], target_lang=payload.language)
        result["suggested_followups"] = [
            translate_from_english(f, target_lang=payload.language) for f in result.get("suggested_followups", [])
        ]
        
    return result