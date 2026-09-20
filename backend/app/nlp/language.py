"""Language detection for en / ta.

No external model: Tamil has its own Unicode block (U+0B80–U+0BFF), which makes script
detection exact. The harder case is Tanglish — Tamil written in Latin letters — which no
Unicode check can catch, so a small marker-word list handles it. Tanglish is reported as
'ta' because a Tanglish speaker wants the Tamil explanation.
"""

from __future__ import annotations

import re

_TAMIL_BLOCK = re.compile(r"[஀-௿]")

# Frequent Tanglish function words. Chosen to avoid collisions with English words.
_TANGLISH_MARKERS = {
    "pannunga", "pannuga", "panunga", "seiyunga", "irukku", "illa",
    "illai", "aagidum", "aagiduchu", "vendam", "venam", "kudunga", "sollunga", "vanga",
    "unga", "ungaluku", "ungalukku", "enna", "epdi", "eppadi", "naalaiku", "indha", "andha",
    "ithu", "adhu", "neenga", "naanga", "avanga", "romba", "konjam", "seri", "aama",
    "anuppunga", "paarunga", "theriyuma", "mudiyum", "mudiyala", "kandippa", "udane",
}

_ENGLISH_STOPWORDS = {
    "the", "is", "are", "you", "your", "to", "and", "for", "of", "in", "on", "with",
    "this", "that", "will", "have", "has", "not", "from", "at", "be", "by", "please",
}


def detect_language(text: str) -> str:
    """Return 'ta' or 'en'. Never raises; empty input defaults to 'en'."""
    if not text or not text.strip():
        return "en"

    tamil_chars = len(_TAMIL_BLOCK.findall(text))
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "en"

    # Any meaningful amount of Tamil script wins: mixed Tamil+English SMS is the norm here,
    # and a user who writes even one Tamil clause should be answered in Tamil.
    if tamil_chars / len(letters) > 0.15:
        return "ta"

    words = set(re.findall(r"[a-z]+", text.lower()))
    tanglish_hits = len(words & _TANGLISH_MARKERS)
    english_hits = len(words & _ENGLISH_STOPWORDS)

    if tanglish_hits >= 2 and tanglish_hits >= english_hits:
        return "ta"
    if tanglish_hits >= 1 and english_hits == 0 and len(words) <= 12:
        return "ta"

    return "en"


def resolve_language(requested: str | None, text: str) -> str:
    """Honour an explicit choice, otherwise detect."""
    if requested in {"en", "ta"}:
        return requested
    return detect_language(text)


def pick(value_en: str, value_ta: str, language: str) -> str:
    return value_ta if language == "ta" else value_en
