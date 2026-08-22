from typing import List, Optional
 
from pydantic import BaseModel
 
from backend.schemas.query_schema import CitationItem
 
 
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
 
 
class ChatSessionRequest(BaseModel):
    session_id: str
    message: str
    language: str = "en"
    history: Optional[List[ChatMessage]] = []
 
 
class ChatSessionResponse(BaseModel):
    status: str = "success"
    session_id: str
    reply: str
    requires_clarification: bool = False
    suggested_followups: List[str] = []
    verdict: Optional[str] = None
    citations: List[CitationItem] = []