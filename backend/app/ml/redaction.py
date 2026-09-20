"""PII redaction.

Every piece of user-submitted text passes through `redact()` before it is stored, logged, or
returned in an API response. This is what lets the app analyse a real scam SMS that a senior
citizen pastes in, without the OTP or account number ever landing in the database.

Order matters: longer/more specific patterns run first so a 16-digit card is not first
chewed up by the 10-digit phone pattern.
"""

from __future__ import annotations

import hashlib
import re

# (name, compiled pattern, placeholder)
_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("aadhaar", re.compile(r"\b[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}\b"), "[REDACTED_AADHAAR]"),
    ("card", re.compile(r"\b(?:\d[ -]?){13,16}\b"), "[REDACTED_CARD]"),
    ("account", re.compile(r"\b\d{9,18}\b"), "[REDACTED_ACCOUNT]"),
    ("ifsc", re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b"), "[REDACTED_IFSC]"),
    ("pan", re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b"), "[REDACTED_PAN]"),
    ("email", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b"), "[REDACTED_EMAIL]"),
    ("upi_vpa", re.compile(r"\b[\w.\-]{2,}@(?:ok\w+|paytm|ybl|axl|upi|ibl|apl|sbi)\b", re.I), "[REDACTED_UPI]"),
    ("phone", re.compile(r"(?:\+?91[\s-]?)?\b[6-9]\d{9}\b"), "[REDACTED_PHONE]"),
    ("cvv", re.compile(r"\b(?:cvv|pin)[\s:]*\d{3,6}\b", re.I), "[REDACTED_PIN]"),
    ("otp", re.compile(r"\b\d{4,8}\b(?=[^\n]{0,40}\b(?:otp|code|password|verification)\b)", re.I), "[REDACTED_OTP]"),
    ("otp_labelled", re.compile(r"\b(?:otp|code|passcode)\b[\s:is]*\b\d{4,8}\b", re.I), "[REDACTED_OTP]"),
]

# UPI VPA must run before the generic email pattern would otherwise swallow it.
_ORDER = [
    "otp_labelled",
    "aadhaar",
    "card",
    "ifsc",
    "pan",
    "upi_vpa",
    "email",
    "phone",
    "account",
    "cvv",
    "otp",
]
_BY_NAME = {name: (pat, repl) for name, pat, repl in _PATTERNS}


def redact(text: str) -> tuple[str, list[str]]:
    """Return (redacted_text, sorted list of PII types found)."""
    if not text:
        return "", []

    found: set[str] = set()
    out = text
    for name in _ORDER:
        pattern, replacement = _BY_NAME[name]

        def _sub(match: re.Match[str], _n=name, _r=replacement) -> str:
            found.add(_n)
            return _r

        out = pattern.sub(_sub, out)

    return out, sorted(found)


def contains_pii(text: str) -> bool:
    _, found = redact(text)
    return bool(found)


def hash_phone(phone: str, salt: str = "cybersathi") -> str:
    """One-way hash so a workshop roster can de-duplicate without storing the number."""
    digits = re.sub(r"\D", "", phone or "")
    if not digits:
        return ""
    return hashlib.sha256(f"{salt}:{digits}".encode()).hexdigest()


def defang_url(url: str) -> str:
    """Make a URL safe to display, store and put in a report — never clickable."""
    return (url or "").replace("http://", "hxxp://").replace("https://", "hxxps://").replace(".", "[.]")


def undefang_url(url: str) -> str:
    """Accept a defanged URL as input so facilitators can paste from awareness material."""
    return (
        (url or "")
        .replace("hxxps://", "https://")
        .replace("hxxp://", "http://")
        .replace("[.]", ".")
        .replace("(.)", ".")
        .replace("[:]", ":")
        .strip()
    )
