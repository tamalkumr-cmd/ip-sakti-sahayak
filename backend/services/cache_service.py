from typing import Dict, Any, Optional

def get_demo_cache(base_url: str = "") -> Dict[str, Dict[str, Any]]:
    clean_base = base_url.rstrip("/") if base_url else "http://localhost:8000"

    return {
        "ashwagandha": {
            "verdict": "Conditional Patentability (Novel Delivery Mechanism)",
            "confidence": 0.94,
            "detailed_analysis": "Under Section 3(p) of the Indian Patent Act 1970, standard extracts of Ashwagandha are excluded as traditional knowledge. However, novel delivery mechanisms (such as nano-emulsions or liposomal complexes) are eligible under Section 3(d) upon providing comparative bio-availability synergy data.",
            "national_compliance": "Requires NBA Form 1 approval under Biological Diversity Act 2002 prior to patent grant, plus Ayush Schedule T GMP licensing.",
            "international_compliance": "Complies with US FDA DSHEA 21 CFR Part 111 cGMP as a dietary supplement. California Proposition 65 heavy metal compliance required.",
            "citations": [
                {
                    "doc_id": "patent_act_1970_sec3",
                    "doc_name": "Indian Patent Act 1970",
                    "regime": "National (India)",
                    "clause_or_section": "Section 3(p) & Section 3(d)",
                    "page_number": 14,
                    "matched_snippet": "An invention which in effect is traditional knowledge or which is an aggregation or duplication of known properties of traditionally known component or components is not patentable.",
                    "pdf_url": f"{clean_base}/api/v1/docs/patent_act_1970_sec3.pdf#page=14"
                },
                {
                    "doc_id": "biological_diversity_act_2002",
                    "doc_name": "Biological Diversity Act 2002",
                    "regime": "National (India)",
                    "clause_or_section": "Section 3 - Access to Bioresources",
                    "page_number": 6,
                    "matched_snippet": "No person who is a non-citizen or foreign entity shall obtain any biological resource occurring in India for research or commercial utilization without approval of National Biodiversity Authority.",
                    "pdf_url": f"{clean_base}/api/v1/docs/biological_diversity_act_2002.pdf#page=6"
                }
            ]
        },
        "triphala": {
            "verdict": "Permitted with Regulatory Compliance Filings",
            "confidence": 0.98,
            "detailed_analysis": "Triphala (Haritaki, Bibhitaki, Amalaki) cannot be patented as a raw mixture due to prior art in TKDL monographs. Export is permitted as an Ayurvedic dietary supplement subject to heavy metal and microbial testing.",
            "national_compliance": "Requires Ayush GMP Schedule T certification, COA from NABL accredited lab, and NBA export clearance.",
            "international_compliance": "US FDA DSHEA compliance with heavy metal limits (Lead < 0.5 ppm) & Proposition 65 warning if sold in California.",
            "citations": [
                {
                    "doc_id": "ayush_gmp_schedule_t",
                    "doc_name": "Ayush GMP Schedule T",
                    "regime": "National (India)",
                    "clause_or_section": "Part 1 - Good Manufacturing Practices",
                    "page_number": 3,
                    "matched_snippet": "Ayurvedic manufacturing premises must comply with sterile raw material handling, batch record logs, and shelf-life stability tests.",
                    "pdf_url": f"{clean_base}/api/v1/docs/ayush_gmp_schedule_t.pdf#page=3"
                }
            ]
        }
    }

def check_cache(query: str, base_url: str = "") -> Optional[Dict[str, Any]]:
    q = query.lower()
    cache = get_demo_cache(base_url)
    for key, data in cache.items():
        if key in q:
            return data
    return None