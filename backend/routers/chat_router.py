from fastapi import APIRouter
from schemas.chat_schema import ChatSessionRequest, ChatSessionResponse
from services.chat_service import process_chat_turn
from services.translation_service import translate_to_english, translate_from_english

router = APIRouter(prefix="/api/v1/chat", tags=["Multi-Turn Consultation"])

@router.post("/message", response_model=ChatSessionResponse)
async def handle_chat_message(payload: ChatSessionRequest):
    # Translate inbound message to English
    eng_message = translate_to_english(payload.message, source_lang=payload.language)

    # Process turn with conversation history context
    result = process_chat_turn(
        session_id=payload.session_id,
        message=eng_message,
        history=payload.history or []
    )

    # Translate outbound reply back if necessary
    if payload.language != "en":
        result["reply"] = translate_from_english(result["reply"], target_lang=payload.language)
        # NOTE: verdict is intentionally NOT translated. It's a status string
        # the frontend may match against exact English values (e.g. for badge
        # rendering — "Patentable", "Barred under 3(p)", etc). Translating it
        # wouldn't crash anything here since it's a plain str, but it WOULD
        # silently break any frontend logic that switches on the exact text.
        result["suggested_followups"] = [
            translate_from_english(f, target_lang=payload.language) for f in result.get("suggested_followups", [])
        ]

    return result