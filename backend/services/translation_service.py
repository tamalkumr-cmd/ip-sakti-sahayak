import re
from deep_translator import GoogleTranslator

LEGAL_TERMS = [
    r"Section\s+3\([a-z]\)",
    r"TKDL",
    r"NBA",
    r"Form\s+1",
    r"Form\s+2",
    r"Schedule\s+T",
    r"21\s+CFR\s+Part\s+111",
    r"Proposition\s+65",
    r"DSHEA",
    r"COA",
    r"Ayush"
]

def translate_to_english(text: str, source_lang: str = "auto") -> str:
    if not text or not text.strip():
        return ""
    if source_lang == "en":
        return text.strip()
    try:
        translated = GoogleTranslator(source=source_lang, target='en').translate(text)
        return translated if translated else text
    except Exception:
        return text

def translate_from_english(text: str, target_lang: str = "en") -> str:
    if not text or not text.strip() or target_lang == "en":
        return text

    # Mask critical legal terms
    placeholders = {}
    modified_text = text
    for i, pattern in enumerate(LEGAL_TERMS):
        matches = re.findall(pattern, modified_text, re.IGNORECASE)
        for m in matches:
            key = f"__LEGAL_{i}__"
            placeholders[key] = m
            modified_text = modified_text.replace(m, key)

    try:
        translated = GoogleTranslator(source='en', target=target_lang).translate(modified_text)
        for key, val in placeholders.items():
            translated = translated.replace(key, val)
        return translated
    except Exception:
        return text