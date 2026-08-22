from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    query: str
    language: str = "en"
    regime_filter: Optional[str] = "all"

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
    detailed_analysis: str
    national_compliance: str
    international_compliance: str
    citations: List[CitationItem]