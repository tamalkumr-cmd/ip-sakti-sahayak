"""
Backend test suite for IP-SAKTI Sahayak.

Run from the repo root with:
    cd backend
    pytest tests/mock_backend_test.py -v

Covers:
  - Health check
  - Query engine: cache hits, RAG fallback, Hindi translation, verdict integrity
  - Multi-turn chat: clarification flow, context-merging across turns, translation
  - Document streaming: existing and missing PDFs
  - PDF export: valid dossier generation

NOTE ON VOICE TESTS: /api/v1/voice/transcribe is intentionally NOT covered here.
It depends on ffmpeg being installed and on real speech audio, neither of which
belong in an automated test suite. Test it manually via Swagger with a real
audio file instead (see project notes).
"""

import sys
import os

# Ensure `backend` (this file's grandparent) is on sys.path the same way
# main.py sets it up, so bare imports like `from main import app` work
# whether pytest is run from the repo root or from inside backend/.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_health_check():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"


# ---------------------------------------------------------------------------
# Query engine
# ---------------------------------------------------------------------------

def test_query_cache_hit_ashwagandha():
    r = client.post("/api/v1/query", json={
        "query": "ashwagandha nano-emulsion patentability",
        "language": "en",
        "regime_filter": "all",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "success"
    assert "ashwagandha" in body["query_in_english"].lower() or "nano-emulsion" in body["query_in_english"].lower()
    assert body["verdict"]
    assert len(body["citations"]) >= 1
    # Every citation must match the CitationItem schema fields
    citation = body["citations"][0]
    for field in ("doc_id", "doc_name", "regime", "clause_or_section", "page_number", "matched_snippet", "pdf_url"):
        assert field in citation


def test_query_response_includes_confidence():
    """Regression test: the frontend's QueryResponse TypeScript interface
    requires a `confidence` field (used by ConfidenceGauge.tsx). Without it,
    the confidence meter component breaks on undefined."""
    r = client.post("/api/v1/query", json={
        "query": "ashwagandha nano-emulsion patentability",
        "language": "en",
    })
    assert r.status_code == 200
    body = r.json()
    assert "confidence" in body
    assert isinstance(body["confidence"], float)
    assert 0.0 <= body["confidence"] <= 1.0


def test_query_cache_hit_triphala():
    r = client.post("/api/v1/query", json={
        "query": "triphala export regulations",
        "language": "en",
    })
    assert r.status_code == 200
    body = r.json()
    assert "triphala" in body["query_in_english"].lower() or "export" in body["query_in_english"].lower()


def test_query_cache_miss_falls_back_gracefully():
    """A query matching neither demo scenario must not crash -- it should
    fall through to ai_bridge's fallback and still return a valid, complete
    QueryResponse rather than a 500 or a partial object."""
    r = client.post("/api/v1/query", json={
        "query": "something totally unrelated xyz123",
        "language": "en",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"]
    assert body["detailed_analysis"]
    assert body["national_compliance"]
    assert body["international_compliance"]
    assert isinstance(body["citations"], list)


def test_query_missing_required_field_returns_422():
    r = client.post("/api/v1/query", json={"language": "en"})  # no `query`
    assert r.status_code == 422


def test_query_verdict_is_not_mangled_by_translation():
    """Regression test for the bug where translating the whole response
    object risked corrupting the verdict field. Verdict must always remain
    a clean, non-empty string even when target language is not English."""
    r = client.post("/api/v1/query", json={
        "query": "ashwagandha nano-emulsion patentability",
        "language": "hi",
    })
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"]
    assert "__LEGAL_" not in body["verdict"]
    assert "{{" not in body["verdict"]


def test_query_hindi_translation_does_not_leak_placeholder_tokens():
    """Regression test for the mask/unmask token bugs found during manual
    testing: translated free-text fields must never contain raw {{N}}
    placeholder tokens -- that would mean a protected term failed to
    restore correctly after translation."""
    r = client.post("/api/v1/query", json={
        "query": "ashwagandha nano-emulsion patentability",
        "language": "hi",
    })
    assert r.status_code == 200
    body = r.json()
    for field in ("detailed_analysis", "national_compliance", "international_compliance"):
        text = body[field]
        assert "{{" not in text, f"Leaked placeholder token in {field}: {text}"
        assert "}}" not in text, f"Leaked placeholder token in {field}: {text}"


# ---------------------------------------------------------------------------
# Multi-turn chat
# ---------------------------------------------------------------------------

def test_chat_first_turn_triggers_clarification():
    r = client.post("/api/v1/chat/message", json={
        "session_id": "test-session-1",
        "message": "I want to patent a turmeric formulation",
        "language": "en",
        "history": [],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["requires_clarification"] is True
    assert len(body["suggested_followups"]) >= 1
    assert body["citations"] == []


def test_chat_second_turn_uses_merged_context():
    """Regression test for the multi-turn context bug: a follow-up answer
    that contains NONE of the original query's keywords must still resolve
    correctly, because the original question gets merged in before the
    cache/RAG lookup. Without the fix, this would silently fall through to
    the generic RAG fallback instead of finding the turmeric-relevant answer."""
    history = [
        {"role": "user", "content": "I want to patent a turmeric formulation for wounds"},
        {"role": "assistant", "content": "Is this a raw extract or an enhanced delivery system?"},
    ]
    r = client.post("/api/v1/chat/message", json={
        "session_id": "test-session-1",
        "message": "It is a traditional herbal paste/extract",
        "language": "en",
        "history": history,
    })
    assert r.status_code == 200
    body = r.json()
    assert body["requires_clarification"] is False
    assert body["verdict"]


def test_chat_pre_answered_query_skips_clarification():
    """If the user already specifies a delivery mechanism in the first
    message, the clarification question should not be asked again."""
    r = client.post("/api/v1/chat/message", json={
        "session_id": "test-session-2",
        "message": "I have a nano-emulsion turmeric formulation",
        "language": "en",
        "history": [],
    })
    assert r.status_code == 200
    body = r.json()
    assert body["requires_clarification"] is False


def test_chat_verdict_not_translated():
    """Same regression as the query engine: verdict must stay untranslated
    even when the chat response itself is localized."""
    r = client.post("/api/v1/chat/message", json={
        "session_id": "test-session-3",
        "message": "ashwagandha anti inflammatory formulation",
        "language": "hi",
        "history": [],
    })
    assert r.status_code == 200
    body = r.json()
    if body["verdict"]:
        assert "{{" not in body["verdict"]
        assert "}}" not in body["verdict"]


def test_chat_missing_required_field_returns_422():
    r = client.post("/api/v1/chat/message", json={"message": "hello"})  # no session_id
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Document streaming
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("doc_id", [
    "patent_act_1970_sec3",
    "biological_diversity_act_2002",
    "ayush_gmp_schedule_t",
])
def test_known_documents_stream_successfully(doc_id):
    r = client.get(f"/api/v1/docs/{doc_id}")
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert int(r.headers["content-length"]) > 0


def test_unknown_document_returns_404():
    r = client.get("/api/v1/docs/nonexistent_document_xyz")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------

def _sample_query_response():
    return {
        "status": "success",
        "query_in_english": "Test query for export",
        "verdict": "Conditional Patentability (Novel Delivery Mechanism)",
        "confidence": 0.85,
        "detailed_analysis": "Sample detailed analysis text.",
        "national_compliance": "Sample national compliance text.",
        "international_compliance": "Sample international compliance text.",
        "citations": [
            {
                "doc_id": "patent_act_1970_sec3",
                "doc_name": "Indian Patent Act 1970",
                "regime": "National (India)",
                "clause_or_section": "Section 3(p)",
                "page_number": 14,
                "matched_snippet": "Sample snippet text for the citation.",
                "pdf_url": "http://localhost:8000/api/v1/docs/patent_act_1970_sec3.pdf#page=14",
            }
        ],
    }


def test_export_pdf_returns_valid_pdf():
    r = client.post("/api/v1/export/pdf", json=_sample_query_response())
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"  # real PDF magic bytes
    assert len(r.content) > 500  # not a near-empty/broken file


def test_export_pdf_handles_empty_citations():
    payload = _sample_query_response()
    payload["citations"] = []
    r = client.post("/api/v1/export/pdf", json=payload)
    assert r.status_code == 200
    assert r.content[:4] == b"%PDF"


def test_export_pdf_missing_required_field_returns_422():
    payload = _sample_query_response()
    del payload["verdict"]
    r = client.post("/api/v1/export/pdf", json=payload)
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# Risk score endpoint
# ---------------------------------------------------------------------------

def _sample_risk_request(novel_delivery=True, sourced_in_india=True, claims=None):
    return {
        "formulation_name": "Ashwa-Curcumin Synergistic Nano-Emulsion",
        "botanical_ingredients": ["Withania somnifera (Ashwagandha)", "Curcuma longa (Haridra)"],
        "is_novel_delivery_system": novel_delivery,
        "therapeutic_claims": claims if claims is not None else ["Enhanced Bioavailability"],
        "bioresource_sourced_in_india": sourced_in_india,
    }


def test_risk_score_returns_valid_shape():
    r = client.post("/api/v1/risk/score", json=_sample_risk_request())
    assert r.status_code == 200
    body = r.json()
    assert body["overall_invalidation_risk"] in ("Low", "Moderate", "High")
    assert 0 <= body["composite_risk_score"] <= 100
    assert len(body["breakdown"]) >= 1
    for item in body["breakdown"]:
        for field in ("category", "risk_level", "score_percentage", "grounds", "remedy_action"):
            assert field in item
        assert item["risk_level"] in ("Low", "Moderate", "High")
        assert 0 <= item["score_percentage"] <= 100


def test_risk_score_novel_delivery_lowers_traditional_knowledge_risk():
    """A novel delivery system should score LOWER Section 3(p) risk than a
    formulation with none -- this is the core logic judges will see explained."""
    r_novel = client.post("/api/v1/risk/score", json=_sample_risk_request(novel_delivery=True))
    r_plain = client.post("/api/v1/risk/score", json=_sample_risk_request(novel_delivery=False))
    assert r_novel.status_code == 200 and r_plain.status_code == 200

    def tk_score(body):
        return next(i["score_percentage"] for i in body["breakdown"] if "3(p)" in i["category"])

    assert tk_score(r_novel.json()) < tk_score(r_plain.json())


def test_risk_score_india_sourced_raises_biodiversity_risk():
    r_india = client.post("/api/v1/risk/score", json=_sample_risk_request(sourced_in_india=True))
    r_foreign = client.post("/api/v1/risk/score", json=_sample_risk_request(sourced_in_india=False))
    assert r_india.status_code == 200 and r_foreign.status_code == 200

    def bd_score(body):
        return next(i["score_percentage"] for i in body["breakdown"] if "Biological Diversity" in i["category"])

    assert bd_score(r_india.json()) > bd_score(r_foreign.json())


def test_risk_score_missing_required_field_returns_422():
    payload = _sample_risk_request()
    del payload["formulation_name"]
    r = client.post("/api/v1/risk/score", json=payload)
    assert r.status_code == 422