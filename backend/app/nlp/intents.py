"""Intent detection for the assistant.

TF-IDF retrieval alone fails badly on the questions people actually type. "my money is gone",
"how do I report", "hi" and "someone hacked my facebook" all scored below threshold and fell
through to an unhelpful "I don't know" — including, worst of all, the victim in distress who
needs the 1930 golden hour *right now*.

This module runs before retrieval and catches those cases deterministically. Intents are
ordered by urgency: EMERGENCY always wins, because a wrong greeting is a small mistake and a
missed victim is not.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class Intent(str, Enum):
    EMERGENCY = "emergency"       # already defrauded — money gone, details shared
    REPORT = "report"             # how / where do I complain
    HELPLINE = "helpline"         # what is 1930, which number to call
    GREETING = "greeting"
    THANKS = "thanks"
    ABOUT = "about"               # who are you, what can you do
    TOPIC = "topic"               # routed to a specific KB article by keyword
    NONE = "none"


@dataclass(frozen=True)
class IntentMatch:
    intent: Intent
    confidence: float
    slug: str | None = None       # for TOPIC, the article to answer from


# --------------------------------------------------------------------- EMERGENCY
# Someone who has already lost money or handed over credentials. Highest priority in the
# whole application: reporting inside the first hour is what lets a bank freeze the transfer.
_EMERGENCY_EN = [
    r"\b(i|we|my (father|mother|friend|wife|husband|son|daughter|uncle|aunt|brother|sister|parents?))\b.{0,40}\b(lost|lose|losing)\b.{0,25}\b(money|rupees|rs|lakh|thousand|amount|savings|\d+)",
    r"\b(money|amount|rupees|rs|cash|savings)\b.{0,30}\b(gone|deducted|debited|taken|stolen|missing|vanished|withdrawn)\b",
    r"\b(i|we)\b.{0,20}\b(got|been|was|were|am)\b.{0,15}\b(scammed|cheated|defrauded|robbed|duped|tricked|hacked)\b",
    r"\b(i|we)\b.{0,25}\b(shared|gave|told|sent|typed|entered)\b.{0,25}\b(otp|pin|cvv|password|card (number|details)|upi pin)\b",
    r"\b(i|we)\b.{0,20}\b(clicked|opened|tapped)\b.{0,20}\b(the )?(link|apk)\b",
    r"\b(i|we)\b.{0,25}\b(installed|downloaded)\b.{0,25}\b(anydesk|teamviewer|quicksupport|the app)\b",
    r"\b(i|we)\b.{0,25}\b(paid|transferred|sent)\b.{0,25}\b(rs\.?\s*\d|₹\s*\d|\d{3,}|money)\b",
    r"\b(fraud|scam)\b.{0,20}\b(happened|occurred)\b",
    r"\bwhat (should|do) i do\b.{0,30}\b(now|money|scam|fraud|otp|lost)\b",
    r"\b(help|save)\s*(me)?\b.{0,20}\b(money|scam|fraud|lost)\b",
]
_EMERGENCY_TA = [
    r"(பணம்|ரூபாய்|தொகை).{0,30}(போய்|போச்சு|எடுக்கப்பட்ட|திருட|இழந்த|கழிக்கப்பட்ட)",
    r"(ஏமாற்ற|மோசடி).{0,25}(பட்ட|ஆகிவிட்ட|நடந்த)",
    r"(நான்|நாங்கள்).{0,25}(otp|ஓடிபி|பின்|கடவுச்சொல்).{0,20}(கொடுத்த|சொன்ன|பகிர்ந்த|அனுப்பிய)",
    r"(என்ன செய்வது|என்ன செய்ய).{0,25}(இப்போது|பணம்|மோசடி)",
    r"(பணம்|ரூபாய்).{0,25}(அனுப்பிவிட்ட|செலுத்திவிட்ட|கட்டிவிட்ட)",
]
# Words that flip an emergency back into a general question: the person is asking
# hypothetically, not reporting a loss.
_HYPOTHETICAL = re.compile(
    r"\b(if|suppose|what if|example|someone might|can someone|is it possible|how do (scammers|they))\b"
    r"|"
    r"(என்றால்|உதாரணமாக|சாத்தியமா)",
    re.IGNORECASE | re.UNICODE,
)

# --------------------------------------------------------------------- REPORT
_REPORT_EN = [
    r"\b(how|where|whom|who)\b.{0,25}\b(to )?(report|complain|complaint|file|register|lodge)\b",
    r"\b(report|complain|complaint|file|lodge|register)\b.{0,25}\b(fraud|scam|cyber|crime|case|fir|online)\b",
    r"\bcybercrime\.gov\.in\b",
    r"\b(file|register|lodge)\b.{0,15}\b(an? )?(fir|case|complaint)\b",
    r"\bcomplaint\b.{0,20}\b(process|procedure|steps|how)\b",
]
_REPORT_TA = [
    r"(எப்படி|எங்கு|யாரிடம்).{0,25}(புகார்|புகாரளி|முறையீடு)",
    r"(புகார்|முறையீடு).{0,25}(அளிக்க|செய்ய|பதிவு)",
]

# --------------------------------------------------------------------- HELPLINE
_HELPLINE_EN = [
    r"\bwhat\b.{0,15}\b(is|number)\b.{0,15}\b1930\b",
    r"\b1930\b.{0,20}\b(number|helpline|what|who|when|means)\b",
    r"\b(helpline|help line|toll free|emergency)\b.{0,20}\b(number|cyber|fraud)\b",
    r"\bwhich number\b.{0,25}\b(call|report|fraud|cyber)\b",
    r"\bwhom to call\b",
]
_HELPLINE_TA = [
    r"1930.{0,25}(என்ன|எண்|யார்|எதற்கு)",
    r"(உதவி எண்|ஹெல்ப்லைன்).{0,20}(என்ன|எது|எந்த)",
]

# --------------------------------------------------------------------- SOCIAL
# No trailing \b on these: a Tamil word can end in a virama (U+0BCD), which is a combining
# mark and therefore not a word character, so \b would never match after "வணக்கம்". The $
# anchor plus the optional punctuation class already stops "hi" from matching "hit".
_GREETING = re.compile(
    r"^\s*(hi|hii+|hey+|hello+|helo|namaste|namaskar|vanakkam|good (morning|afternoon|evening)"
    r"|வணக்கம்|ஹாய்|ஹலோ)[\s!.,]*$",
    re.IGNORECASE | re.UNICODE,
)
_THANKS = re.compile(
    r"^\s*(thanks?|thank you|thx|tq|nandri|நன்றி|மிக்க நன்றி|super|ok|okay|good|nice|great)"
    r"[\s!.,]*$",
    re.IGNORECASE | re.UNICODE,
)
_ABOUT = re.compile(
    r"\b(who are you|what are you|what can you do|what is this (app|tool|site)|how do you work"
    r"|your name|about you|help me with what)\b"
    r"|(நீ யார்|இது என்ன (செயலி|தளம்)|என்ன செய்ய முடியும்)",
    re.IGNORECASE | re.UNICODE,
)

# --------------------------------------------------------------------- TOPIC ROUTING
# Deterministic keyword -> article. This is the backstop for everything TF-IDF misses:
# brand names, platform names and colloquial phrasing that never appear in article prose.
TOPIC_KEYWORDS: list[tuple[str, list[str]]] = [
    ("otp-scams", [
        "otp", "one time password", "ஓடிபி", "verification code", "6 digit", "six digit",
    ]),
    ("kyc-scams", [
        "kyc", "கேஒய்சி", "re-kyc", "rekyc", "know your customer", "aadhaar link", "pan update",
    ]),
    ("job-scams", [
        "job", "work from home", "part time", "task", "vacancy", "hiring", "interview fee",
        "registration fee", "placement", "வேலை", "ஜாப்", "salary offer", "earn daily",
    ]),
    ("investment-scams", [
        "investment", "invest", "trading", "crypto", "bitcoin", "forex", "stock", "share market",
        "mutual fund", "double money", "returns", "profit", "sebi", "முதலீடு", "லாபம்",
    ]),
    ("banking-scams", [
        "bank", "card", "cvv", "debit", "credit card", "net banking", "netbanking", "atm",
        "anydesk", "teamviewer", "screen share", "customer care", "வங்கி", "கார்டு",
    ]),
    ("loan-scams", [
        "loan", "lending", "emi", "cibil", "loan app", "borrow", "instant loan", "கடன்",
        "harass", "threatening", "abusive", "contacts", "morph",
    ]),
    ("impersonation-scams", [
        "electricity", "eb bill", "power cut", "tneb", "sim", "trai", "army", "officer",
        "new number", "relative", "uncle", "mummy", "gas subsidy", "மின்சாரம்", "சிம்",
    ]),
    ("social-media-scams", [
        "facebook", "instagram", "whatsapp", "twitter", "youtube", "snapchat", "telegram",
        "account hacked", "hacked", "profile", "blackmail", "video call", "nude", "sextortion",
        "private video", "leak", "முகநூல்", "சமூக ஊடக",
    ]),
    ("digital-arrest-scams", [
        "digital arrest", "cbi", "ed ", "enforcement", "police call", "narcotics", "ncb",
        "court", "warrant", "custody", "skype", "டிஜிட்டல் கைது", "சிபிஐ",
    ]),
    ("courier-parcel-scams", [
        "parcel", "courier", "fedex", "dhl", "customs", "consignment", "shipment", "delivery",
        "blue dart", "பார்சல்", "கூரியர்",
    ]),
    ("lottery-prize-scams", [
        "lottery", "lucky draw", "prize", "won", "winner", "jackpot", "kbc", "bumper",
        "லாட்டரி", "பரிசு",
    ]),
    ("upi-qr-safety", [
        "upi", "qr", "scan", "gpay", "google pay", "phonepe", "paytm", "bhim", "collect request",
        "upi pin", "cashback", "refund", "யுபிஐ", "ஸ்கேன்",
    ]),
]


def _any(patterns: list[str], text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE | re.UNICODE) for p in patterns)


def detect(question: str) -> IntentMatch:
    """Classify the question. Ordered by urgency — emergency first, always."""
    if not question or not question.strip():
        return IntentMatch(Intent.NONE, 0.0)

    q = question.strip()
    lower = q.lower()

    # 1. EMERGENCY — someone has already been defrauded.
    if (_any(_EMERGENCY_EN, lower) or _any(_EMERGENCY_TA, q)) and not _HYPOTHETICAL.search(q):
        return IntentMatch(Intent.EMERGENCY, 1.0)

    # 2. Short social turns. Checked before topic routing so "ok" does not match a keyword.
    if _GREETING.match(q):
        return IntentMatch(Intent.GREETING, 1.0)
    if _THANKS.match(q):
        return IntentMatch(Intent.THANKS, 1.0)
    if _ABOUT.search(q):
        return IntentMatch(Intent.ABOUT, 0.9)

    # 3. Reporting and helpline — core functions that were falling through.
    if _any(_REPORT_EN, lower) or _any(_REPORT_TA, q):
        return IntentMatch(Intent.REPORT, 0.95)
    if _any(_HELPLINE_EN, lower) or _any(_HELPLINE_TA, q):
        return IntentMatch(Intent.HELPLINE, 0.95)

    # 4. Keyword routing to a specific article.
    best_slug, best_hits = None, 0
    for slug, keywords in TOPIC_KEYWORDS:
        hits = sum(1 for kw in keywords if kw in lower or kw in q)
        if hits > best_hits:
            best_slug, best_hits = slug, hits

    if best_slug and best_hits > 0:
        # More matched keywords means a more confident route.
        return IntentMatch(Intent.TOPIC, min(0.55 + 0.15 * best_hits, 0.95), best_slug)

    return IntentMatch(Intent.NONE, 0.0)


def expand_query(question: str) -> str:
    """Add related terms so short queries match article prose.

    "hacked facebook" shares almost no vocabulary with an article that says "account theft"
    and "password". Appending the matched topic's keywords closes that gap for TF-IDF.
    """
    lower = question.lower()
    extra: list[str] = []
    for slug, keywords in TOPIC_KEYWORDS:
        if any(kw in lower for kw in keywords):
            extra.append(slug.replace("-", " "))
            extra.extend(keywords[:6])
    return f"{question} {' '.join(extra)}" if extra else question
