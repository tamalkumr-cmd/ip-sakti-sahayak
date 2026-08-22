from pydantic import BaseModel, Field
from typing import List, Optional

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Ayush IP or regulatory question")
    language: str = "en"
    regime_filter: str = "all"

class CitationItem(BaseModel):
    doc_id: str
    doc_name: str
    regime: str
    clause_or_section: str
    page_number: int
    matched_snippet: str
    pdf_url: str

class QueryResponse(BaseModel):
    status: str = "success"
    query_in_english: str
    verdict: str
    confidence: float = 0.95
    detailed_analysis: str
    national_compliance: str
    international_compliance: str
    citations: List[CitationItem] = []