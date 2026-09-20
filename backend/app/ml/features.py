"""Static feature extraction for URLs and text.

Hard safety rule: nothing in this module ever opens a network connection. Every feature is
computed from the URL string itself. A phishing checker that fetches the URL would (a) confirm
to the attacker that a human read the message, and (b) risk executing a drive-by payload on a
student's laptop during a demo.
"""

from __future__ import annotations

import math
import re
from urllib.parse import urlparse

SUSPICIOUS_TLDS = {
    "tk", "ml", "ga", "cf", "gq", "xyz", "top", "buzz", "click", "zip", "mov", "work",
    "loan", "men", "date", "racing", "win", "review", "country", "stream", "download",
    "icu", "cyou", "rest", "fit", "cam", "sbs", "lol", "quest",
}

SHORTENERS = {
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "rb.gy", "cutt.ly", "is.gd", "ow.ly",
    "shorturl.at", "rebrand.ly", "tiny.cc", "surl.li", "clck.ru", "shorte.st", "t.ly",
}

BRAND_KEYWORDS = [
    "sbi", "hdfc", "icici", "axis", "kotak", "pnb", "canara", "bob", "yesbank", "idfc",
    "paytm", "phonepe", "gpay", "googlepay", "bhim", "upi", "npci", "rbi",
    "amazon", "flipkart", "netflix", "irctc", "epfo", "uidai", "aadhaar", "incometax",
    "whatsapp", "facebook", "instagram", "jio", "airtel", "vodafone", "bsnl",
]

SENSITIVE_WORDS = [
    "login", "signin", "verify", "verification", "kyc", "update", "secure", "security",
    "account", "otp", "wallet", "refund", "confirm", "validate", "authenticate",
    "netbanking", "password", "unlock", "suspend", "reward", "prize", "claim", "offer",
]

_IP_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")
_HEX_IP_RE = re.compile(r"^0x[0-9a-f]+$", re.I)

FEATURE_NAMES = [
    "url_length", "hostname_length", "path_depth", "num_dots", "num_hyphens", "num_digits",
    "digit_ratio", "has_ip_host", "has_at_symbol", "num_subdomains", "is_https",
    "port_present", "suspicious_tld", "shortener_flag", "brand_keyword_hit",
    "sensitive_word_hit", "host_entropy", "has_punycode", "hyphen_in_domain",
    "double_slash_in_path", "query_param_count", "is_typosquat", "tld_length",
    "longest_token_length", "num_special_chars",
]


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def _levenshtein(a: str, b: str, cap: int = 3) -> int:
    """Small bounded edit distance — enough to spot 'arnazon' vs 'amazon'."""
    if abs(len(a) - len(b)) > cap:
        return cap + 1
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
        if min(prev) > cap:
            return cap + 1
    return prev[-1]


def normalise_url(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://", url):
        url = "http://" + url
    return url


def extract_url_features(url: str) -> dict[str, float]:
    """Return the full static feature dict. Never raises on malformed input."""
    url = normalise_url(url)
    try:
        parsed = urlparse(url)
    except ValueError:
        parsed = urlparse("http://invalid.invalid")

    host = (parsed.hostname or "").lower()
    path = parsed.path or ""
    query = parsed.query or ""
    full = url.lower()

    labels = [p for p in host.split(".") if p]
    tld = labels[-1] if len(labels) > 1 else ""
    domain = labels[-2] if len(labels) >= 2 else (labels[0] if labels else "")

    num_digits = sum(c.isdigit() for c in url)
    is_ip = bool(_IP_RE.match(host) or _HEX_IP_RE.match(host))

    typosquat = 0
    if domain and domain not in BRAND_KEYWORDS:
        for brand in BRAND_KEYWORDS:
            if len(brand) >= 4 and 0 < _levenshtein(domain, brand) <= 2:
                typosquat = 1
                break

    tokens = re.split(r"[^a-zA-Z0-9]+", full)
    longest_token = max((len(t) for t in tokens), default=0)

    return {
        "url_length": float(len(url)),
        "hostname_length": float(len(host)),
        "path_depth": float(len([p for p in path.split("/") if p])),
        "num_dots": float(host.count(".")),
        "num_hyphens": float(url.count("-")),
        "num_digits": float(num_digits),
        "digit_ratio": round(num_digits / len(url), 4) if url else 0.0,
        "has_ip_host": float(is_ip),
        "has_at_symbol": float("@" in url),
        "num_subdomains": float(max(0, len(labels) - 2)),
        "is_https": float(parsed.scheme == "https"),
        "port_present": float(parsed.port is not None),
        "suspicious_tld": float(tld in SUSPICIOUS_TLDS),
        "shortener_flag": float(host in SHORTENERS),
        "brand_keyword_hit": float(any(b in full for b in BRAND_KEYWORDS)),
        "sensitive_word_hit": float(sum(w in full for w in SENSITIVE_WORDS)),
        "host_entropy": round(_shannon_entropy(host), 4),
        "has_punycode": float("xn--" in host),
        "hyphen_in_domain": float("-" in domain),
        "double_slash_in_path": float("//" in path),
        "query_param_count": float(len([q for q in query.split("&") if q])),
        "is_typosquat": float(typosquat),
        "tld_length": float(len(tld)),
        "longest_token_length": float(longest_token),
        "num_special_chars": float(sum(url.count(c) for c in "?=&%_~")),
    }


def features_to_vector(feats: dict[str, float]) -> list[float]:
    return [float(feats.get(name, 0.0)) for name in FEATURE_NAMES]


def detect_lookalike_brand(url: str) -> str | None:
    """Which brand is this URL pretending to be, if any."""
    url_l = normalise_url(url).lower()
    parsed = urlparse(url_l)
    host = (parsed.hostname or "").lower()
    labels = [p for p in host.split(".") if p]
    if len(labels) < 2:
        return None

    registered = ".".join(labels[-2:])
    domain = labels[-2]

    official = {
        "sbi": "onlinesbi.sbi", "hdfc": "hdfcbank.com", "icici": "icicibank.com",
        "paytm": "paytm.com", "phonepe": "phonepe.com", "amazon": "amazon.in",
        "flipkart": "flipkart.com", "irctc": "irctc.co.in", "epfo": "epfindia.gov.in",
        "uidai": "uidai.gov.in", "netflix": "netflix.com", "rbi": "rbi.org.in",
    }

    for brand, real_domain in official.items():
        if registered == real_domain:
            return None  # it IS the real site
        # brand name appears somewhere in the host but the registered domain is not theirs
        if brand in host and registered != real_domain:
            return brand.upper()
        if len(brand) >= 4 and 0 < _levenshtein(domain, brand) <= 2:
            return brand.upper()
    return None


# ---------------------------------------------------------------- text side features

_URGENCY = ["immediately", "urgent", "hurry", "now", "today", "expire", "last", "final",
            "உடனே", "அவசரம்", "இன்றே", "கடைசி"]
_THREAT = ["block", "suspend", "freeze", "arrest", "legal", "penalty", "fine", "disconnect",
           "முடக்க", "கைது", "அபராதம்", "நிறுத்த"]
_REWARD = ["win", "won", "prize", "reward", "cashback", "bonus", "free", "gift", "lottery",
           "பரிசு", "வெற்றி", "இலவச", "போனஸ்"]


def extract_text_side_features(text: str) -> dict[str, float]:
    """Numeric signals that complement TF-IDF (which only sees token frequencies)."""
    t = (text or "").lower()
    letters = [c for c in (text or "") if c.isalpha()]
    caps = [c for c in letters if c.isupper()]
    return {
        "has_link": float(bool(re.search(r"https?://|www\.|\[\.\]", t))),
        "has_phone": float(bool(re.search(r"\b[6-9]\d{9}\b|\[REDACTED_PHONE\]", text or ""))),
        "has_amount": float(bool(re.search(r"(rs\.?\s*\d|₹\s*\d|\d+\s*(lakh|crore|rupees))", t))),
        "urgency_count": float(sum(w in t for w in _URGENCY)),
        "threat_count": float(sum(w in t for w in _THREAT)),
        "reward_count": float(sum(w in t for w in _REWARD)),
        "exclamation_count": float((text or "").count("!")),
        "all_caps_ratio": round(len(caps) / len(letters), 4) if letters else 0.0,
        "length": float(len(text or "")),
    }


TEXT_SIDE_FEATURE_NAMES = [
    "has_link", "has_phone", "has_amount", "urgency_count", "threat_count",
    "reward_count", "exclamation_count", "all_caps_ratio", "length",
]
