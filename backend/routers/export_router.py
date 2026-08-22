from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from schemas.query_schema import QueryResponse
from services.export_service import generate_compliance_pdf

router = APIRouter(prefix="/api/v1/export", tags=["Dossier Export"])

@router.post("/pdf")
async def export_dossier_pdf(payload: QueryResponse):
    try:
        pdf_buffer = generate_compliance_pdf(payload.model_dump())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {exc}")
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=IP_SAKTI_Compliance_Dossier.pdf"
        }
    )