import re
from typing import Tuple, Dict
from deep_translator import GoogleTranslator

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
    mask_map = {}
    masked_text = text
    for i, pattern in enumerate(PROTECTED_TERMS):
        matches = re.findall(pattern, masked_text, flags=re.IGNORECASE)
        for match in set(matches):
            token = f"__LEGAL_{i}__"
            masked_text = masked_text.replace(match, token)
            mask_map[token] = match
    return masked_text, mask_map

def unmask_legal_terms(text: str, mask_map: Dict[str, str]) -> str:
    unmasked = text
    for token, original in mask_map.items():
        unmasked = unmasked.replace(token, original)
    return unmasked

def translate_to_english(text: str, source_lang: str = "auto") -> str:
    if source_lang == "en" or not text.strip():
        return text
    try:
        masked, _ = mask_legal_terms(text)
        translated = GoogleTranslator(source=source_lang, target="en").translate(masked)
        return translated
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