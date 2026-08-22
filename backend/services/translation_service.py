import logging
import re
from typing import Tuple, Dict
from deep_translator import GoogleTranslator

logger = logging.getLogger("ip_sakti_backend.translation")

# Regulatory and botanical terms that must NEVER be translated into regional text
PROTECTED_TERMS = [
    r"Section 3\(p\)",
    r"Section 3\(d\)",
    r"Section 19",
    r"TKDL",
    r"NBA",
    r"Schedule T",
    r"21 CFR Part 111",
    r"Form 1",
    r"Form 2",
    r"Withania somnifera",
    r"Curcuma longa",
    r"THMPD",
    r"Ayush",
    r"US FDA"
]


def mask_legal_terms(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Replaces protected legal/scientific terms with unique placeholder tokens.

    BUG FIX #1 (token collision): the original version generated the token
    from the pattern index alone (__LEGAL_{i}__), so if the same pattern
    matched two different-case variants in one text (e.g. "Ayush" and
    "AYUSH" both appearing), both distinct strings collided on the same
    token. Fixed with a running counter unique per distinct match.

    BUG FIX #2 (translatable token text) — found via live testing with a
    real Hindi query: the token "__LEGAL_0__" contains the real English
    word "LEGAL", and Google Translate happily translated THAT word too,
    turning "__LEGAL_2__" into "_कानूनी_2_" mid-translation. unmask_legal_terms
    then searched for the original "__LEGAL_2__" string, didn't find it
    (since it had been mangled), and silently failed to restore "NBA" /
    "Form 1" / etc. — leaving the broken placeholder in the final response.
    Token format is now pure digits in double braces ("{{0}}", "{{1}}", ...)
    with no dictionary words for the translator to latch onto.
    """
    mask_map: Dict[str, str] = {}
    masked_text = text
    counter = 0

    for pattern in PROTECTED_TERMS:
        matches = re.findall(pattern, masked_text, flags=re.IGNORECASE)
        for match in set(matches):
            token = f"{{{{{counter}}}}}"  # -> "{{0}}", "{{1}}", ...
            counter += 1
            masked_text = masked_text.replace(match, token)
            mask_map[token] = match

    return masked_text, mask_map


def unmask_legal_terms(text: str, mask_map: Dict[str, str]) -> str:
    unmasked = text
    for token, original in mask_map.items():
        if token not in unmasked:
            # The translator altered the token itself (spacing, mid-token
            # word substitution, etc.) — this is exactly the class of bug
            # that caused mangled "_कानूनी_2_" placeholders to leak into
            # responses. Logging it means a future translator quirk shows
            # up in server logs instead of shipping broken text silently.
            logger.warning(
                "Mask token %r not found in translated text — protected "
                "term %r may not have been restored correctly.",
                token, original,
            )
        unmasked = unmasked.replace(token, original)
    return unmasked


def translate_to_english(text: str, source_lang: str = "auto") -> str:
    """
    BUG FIXED: previously masked the input but discarded the mask_map
    (`masked, _ = mask_legal_terms(text)`) and never unmasked the
    translated result. Any protected term embedded in a non-English query
    (e.g. a Hindi query that mentions "TKDL" or "Section 3(p)" verbatim)
    would come back from translation with a raw, unresolved placeholder
    token sitting in the middle of the English text — corrupting
    both the RAG query and anything that later displays query_in_english
    (e.g. the exported PDF's "Subject Query" field).
    """
    if source_lang == "en" or not text.strip():
        return text
    try:
        masked, mask_map = mask_legal_terms(text)
        translated = GoogleTranslator(source=source_lang, target="en").translate(masked)
        return unmask_legal_terms(translated, mask_map)
    except Exception:
        return text


def translate_from_english(text: str, target_lang: str = "en") -> str:
    if target_lang == "en" or not text.strip():
        return text
    try:
        masked, mask_map = mask_legal_terms(text)
        translated = GoogleTranslator(source="en", target=target_lang).translate(masked)
        return unmask_legal_terms(translated, mask_map)
    except Exception:
        return text