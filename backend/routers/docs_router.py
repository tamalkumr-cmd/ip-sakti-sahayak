import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/v1/docs", tags=["Documents"])
PDF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ai_engine/data/raw_pdfs"))

@router.get("/{doc_id}")
async def serve_pdf(doc_id: str):
    clean_id = doc_id if doc_id.endswith(".pdf") else f"{doc_id}.pdf"
    file_path = os.path.join(PDF_DIR, clean_id)
    
    if not os.path.exists(file_path):
        os.makedirs(PDF_DIR, exist_ok=True)
        raise HTTPException(status_code=404, detail=f"PDF document '{clean_id}' not found.")
        
    return FileResponse(file_path, media_type="application/pdf", filename=clean_id)