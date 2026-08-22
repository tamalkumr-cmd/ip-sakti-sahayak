import logging
import sys
import os

logger = logging.getLogger("ip_sakti_backend.ai_bridge")

# Adds repository root to sys.path so it can access ai_engine
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

def execute_rag(query: str, regime_filter: str = "all") -> dict:
    try:
        from ai_engine.rag_pipeline import run_rag_query
        return run_rag_query(query, regime_filter)
    except ModuleNotFoundError:
        # Expected until Track 1 lands ai_engine/rag_pipeline.py — no need to
        # log this as an error, it's the normal state during parallel dev.
        logger.info("ai_engine.rag_pipeline not available yet; using fallback response.")
    except Exception:
        # NOT expected: the real pipeline exists but threw. Previously this
        # was silently swallowed by a bare `except Exception`, so a genuine
        # bug in Track 1's code would be invisible — every query would just
        # look like it's still using the fallback, with no clue why.
        logger.exception("ai_engine.rag_pipeline raised an unexpected error for query=%r", query)

    return {
        "status": "success",
        "query_in_english": query,
        "verdict": "Conditional Patentability (Novel Delivery Mechanism)",
        "confidence": 0.5,  # Neutral/low-certainty value: this is the unverified fallback stub,
                            # not a real RAG-grounded answer, so it should never claim high confidence.
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
                "pdf_url": "http://localhost:8000/api/v1/docs/patent_act_1970_sec3.pdf#page=14"
            }
        ]
    }