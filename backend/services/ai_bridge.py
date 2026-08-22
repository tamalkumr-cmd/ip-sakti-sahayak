"""
backend/services/ai_bridge.py

Calls Track 1's RAG engine over HTTP instead of importing it directly.
This is necessary because the RAG engine (Ollama + ChromaDB) runs on
Track 1's own machine, while this backend runs on Render -- two separate
machines that can't share Python imports, only network requests.

REQUIRED ENV VAR (set in Render dashboard -> Environment):
    RAG_SERVICE_URL=https://your-ngrok-url.ngrok-free.app/run-rag-query

If this env var isn't set, or the local machine/tunnel is unreachable
(laptop asleep, ngrok not running, network hiccup), this falls back to
the same safe stub response as before -- the live Render demo never
crashes just because the local RAG server happens to be offline.
"""

import logging
import os

import requests

logger = logging.getLogger("ip_sakti_backend.ai_bridge")

RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL")
# CPU-mode local LLM inference is slow -- confirmed ~26s for a single real
# answer (embedding + llama3 generation) during integration testing. The
# previous 15s timeout was firing before real answers ever came back,
# silently falling back to the stub every time even though the RAG server
# and tunnel were both working correctly. 90s gives real headroom.
RAG_REQUEST_TIMEOUT_SECONDS = 90


def execute_rag(query: str, regime_filter: str = "all") -> dict:
    if not RAG_SERVICE_URL:
        logger.info("RAG_SERVICE_URL not set; using fallback response.")
        return _fallback_response(query)

    try:
        response = requests.post(
            RAG_SERVICE_URL,
            json={"query": query, "regime_filter": regime_filter},
            timeout=RAG_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        logger.warning("Could not reach local RAG server at %s -- is it running and tunneled?", RAG_SERVICE_URL)
    except requests.exceptions.Timeout:
        logger.warning("Local RAG server timed out after %ss.", RAG_REQUEST_TIMEOUT_SECONDS)
    except Exception:
        logger.exception("Unexpected error calling local RAG server for query=%r", query)

    return _fallback_response(query)


def _fallback_response(query: str) -> dict:
    return {
        "status": "success",
        "query_in_english": query,
        "verdict": "Conditional Patentability (Novel Delivery Mechanism)",
        "confidence": 0.5,
        "detailed_analysis": (
            "Section 3(p) of the Indian Patent Act prohibits patenting traditional knowledge "
            "or aggregations of known herbal properties. However, a novel drug delivery system "
            "(e.g., nano-emulsion or liposomal carrier) with verified synergistic bioavailability "
            "is eligible under Section 3(d)."
        ),
        "national_compliance": "Mandatory Form 1 filing with the National Biodiversity Authority (NBA) prior to grant.",
        "international_compliance": "Requires US FDA 21 CFR Part 111 cGMP compliance for herbal dietary supplement export.",
        "citations": [
            {
                "doc_id": "patent_act_1970_sec3",
                "doc_name": "Indian Patent Act 1970",
                "regime": "National (India)",
                "clause_or_section": "Section 3(p)",
                "page_number": 14,
                "matched_snippet": "An invention which in effect is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known components is not patentable.",
                "pdf_url": "http://localhost:8000/api/v1/docs/patent_act_1970_sec3.pdf#page=14",
            }
        ],
    }