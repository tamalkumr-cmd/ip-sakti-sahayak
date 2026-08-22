import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def generate_compliance_pdf(data: dict) -> io.BytesIO:
    """
    Builds the compliance dossier PDF from a dict matching the real
    QueryResponse contract (backend/schemas/query_schema.py):

        status, query_in_english, verdict, detailed_analysis,
        national_compliance, international_compliance, citations (List[CitationItem])

    Pass response.model_dump() from a QueryResponse instance (this is what
    export_router.py does — the frontend must POST back the full response
    object it received from /query or /chat/message).
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "DocTitle", parent=styles["Heading1"], fontSize=18, leading=22,
        textColor=colors.HexColor("#065f46"),
    )
    section_heading = ParagraphStyle(
        "SectionHeading", parent=styles["Heading2"], fontSize=12, leading=16,
        textColor=colors.HexColor("#0f766e"), spaceBefore=10, spaceAfter=4,
    )
    body_style = ParagraphStyle(
        "BodyDark", parent=styles["Normal"], fontSize=9, leading=13,
        textColor=colors.HexColor("#1e293b"),
    )

    story = []

    # --- Title & metadata --------------------------------------------
    story.append(Paragraph("<b>IP-SAKTI Sahayak — Regulatory Compliance Dossier</b>", title_style))
    story.append(Paragraph("<i>Ministry of Ayush &amp; Intellectual Property Compliance Advisory</i>", body_style))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#059669"), spaceAfter=12))

    # --- Query & verdict ------------------------------------------------
    story.append(Paragraph("<b>Subject Query:</b>", section_heading))
    story.append(Paragraph(_esc(data.get("query_in_english", "N/A")), body_style))
    story.append(Spacer(1, 8))

    story.append(Paragraph("<b>Legal Verdict:</b>", section_heading))
    story.append(Paragraph(f"<b>{_esc(data.get('verdict', 'N/A'))}</b>", body_style))
    story.append(Spacer(1, 4))
    confidence = data.get("confidence")
    if confidence is not None:
        story.append(Paragraph(f"Confidence score: {confidence:.0%}", body_style))
    story.append(Spacer(1, 8))

    # --- Analysis ---------------------------------------------------------
    story.append(Paragraph("<b>Detailed Legal &amp; Regulatory Analysis:</b>", section_heading))
    story.append(Paragraph(_esc(data.get("detailed_analysis", "N/A")), body_style))
    story.append(Spacer(1, 8))

    # --- Compliance breakdown table -----------------------------------
    story.append(Paragraph("<b>Jurisdiction Compliance Matrix:</b>", section_heading))
    table_data = [
        [
            Paragraph("<b>National Regime (India)</b>", body_style),
            Paragraph(_esc(data.get("national_compliance", "N/A")), body_style),
        ],
        [
            Paragraph("<b>International Regime</b>", body_style),
            Paragraph(_esc(data.get("international_compliance", "N/A")), body_style),
        ],
    ]
    t = Table(table_data, colWidths=[150, 380])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # --- Citations -----------------------------------------------------
    citations = data.get("citations", [])
    if citations:
        story.append(Paragraph("<b>Statutory Citations &amp; Gazette References:</b>", section_heading))
        cite_table_data = [[
            Paragraph("<b>Document</b>", body_style),
            Paragraph("<b>Section / Clause</b>", body_style),
            Paragraph("<b>Page</b>", body_style),
            Paragraph("<b>Snippet</b>", body_style),
        ]]
        for c in citations:
            snippet = c.get("matched_snippet", "") or ""
            snippet_display = snippet[:120] + ("..." if len(snippet) > 120 else "")
            cite_table_data.append([
                Paragraph(_esc(c.get("doc_name", "N/A")), body_style),
                Paragraph(_esc(c.get("clause_or_section", "N/A")), body_style),
                Paragraph(str(c.get("page_number", "-")), body_style),
                Paragraph(_esc(snippet_display), body_style),
            ])
        ct = Table(cite_table_data, colWidths=[130, 110, 40, 250])
        ct.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(ct)

    doc.build(story)
    buffer.seek(0)
    return buffer


def _esc(text) -> str:
    """Escapes text for safe use inside a reportlab Paragraph (parses a mini-HTML subset)."""
    if text is None:
        return "N/A"
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")