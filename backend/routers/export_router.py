from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from schemas.query_schema import QueryResponse
from services.export_service import generate_compliance_pdf

router = APIRouter(prefix="/api/v1/export", tags=["Dossier Export"])

@router.post("/pdf")
async def export_dossier_pdf(payload: QueryResponse):
    pdf_buffer = generate_compliance_pdf(payload.model_dump())
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=IP_SAKTI_Compliance_Dossier.pdf"
        }
    )