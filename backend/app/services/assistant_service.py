"""The multilingual assistant.

Resolution order:
    1. safety gate          refuse scam-generation and hacking requests
    2. EMERGENCY intent     someone already defrauded -> golden-hour steps, highest priority
    3. pasted content       a message or URL -> route to the analyzer
    4. other intents        report / helpline / greeting / thanks / about
    5. keyword topic route  deterministic keyword -> article
    6. KB retrieval         TF-IDF over the knowledge base, with query expansion
    7. optional local LLM   grounded strictly in the retrieved article
    8. fallback             an honest "not sure" that still lists what I can do

Steps 1-6 and 8 are deterministic, so the assistant is fully functional with no model, no key
and no internet.

The intent layer (step 2, 4, 5) exists because retrieval alone failed the questions people
actually type. Before it, "my money is gone", "how do I report", "someone hacked my facebook"
and "hi" all scored below the similarity threshold and returned "I don't have a confident
answer" — including, worst of all, the victim in distress who needs 1930 immediately.
"""

from __future__ import annotations

import logging
import re

from sqlalchemy.orm import Session

from app.config import settings
from app.ml import redaction
from app.models import AssistantLog, KbArticle
from app.nlp import intents, responses, retriever
from app.nlp.intents import Intent
from app.nlp.language import resolve_language
from app.services import scam_service, url_service

logger = logging.getLogger(__name__)

MIN_KB_SCORE = 0.12

DISCLAIMER = {
    "en": "General awareness guidance only. For an actual fraud, call 1930 or report at cybercrime.gov.in.",
    "ta": "பொது விழிப்புணர்வு தகவல் மட்டுமே. உண்மையான மோசடிக்கு 1930-ஐ அழையுங்கள் அல்லது cybercrime.gov.in-ல் புகார் அளியுங்கள்.",
}

# Requests the assistant must refuse. The app teaches defence; it does not produce scam content
# or help with vigilante "recovery", which is itself a common secondary fraud.
_REFUSAL_PATTERNS = [
    r"\b(write|create|generate|compose|draft|make)\b.{0,30}\b(scam|phishing|fraud|fake)\b.{0,20}\b(message|sms|email|text|letter|link|page|site)\b",
    r"\b(how to|teach me to|help me)\b.{0,25}\b(scam|cheat|defraud|phish|hack)\b.{0,20}\b(someone|people|person|bank|account)\b",
    r"\b(hack|crack|break into)\b.{0,25}\b(account|phone|whatsapp|facebook|instagram|password|otp)\b",
    r"\b(trace|track|find)\b.{0,25}\b(scammer|fraudster)\b.{0,25}\b(myself|own|revenge|teach.*lesson)\b",
    r"\bfake\b.{0,20}\b(otp|bank message|payment screenshot|receipt)\b",
]

REFUSAL_ANSWER = {
    "en": (
        "I can't help create scam or phishing content, or with hacking into an account — "
        "including your own scammer's.\n\n"
        "If you are trying to recover money you lost: call 1930 immediately and file a report "
        "at cybercrime.gov.in. Reporting within the first hour gives the best chance of the "
        "money being frozen.\n\n"
        "Be careful of anyone who offers to 'recover' your money for a fee — that is a common "
        "second scam targeting people who have already been cheated.\n\n"
        "I'm happy to explain how any of these scams work so you can recognise and avoid them."
    ),
    "ta": (
        "மோசடி அல்லது ஃபிஷிங் உள்ளடக்கம் உருவாக்கவோ, கணக்கை ஹேக் செய்யவோ நான் உதவ முடியாது.\n\n"
        "இழந்த பணத்தை மீட்க முயன்றால்: உடனே 1930-ஐ அழைத்து cybercrime.gov.in-ல் புகார் அளியுங்கள். "
        "முதல் ஒரு மணி நேரத்தில் புகாரளித்தால் பணத்தை முடக்க வாய்ப்பு அதிகம்.\n\n"
        "கட்டணம் வாங்கி பணத்தை 'மீட்டுத் தருவதாக' கூறுபவர்களிடம் கவனமாக இருங்கள் — "
        "ஏற்கனவே ஏமாந்தவர்களை குறி வைக்கும் இரண்டாவது மோசடி இது.\n\n"
        "இந்த மோசடிகள் எப்படி வேலை செய்கின்றன என்பதை விளக்க நான் தயார்."
    ),
}

SUGGESTIONS = {
    "en": [
        "Someone is asking for my OTP. What should I do?",
        "I got an SMS saying my KYC has expired. Is it real?",
        "A job offer is asking me to pay a registration fee.",
        "Do I need to scan a QR code to receive money?",
        "What is a digital arrest?",
        "How do I report a cyber fraud in India?",
        "Is it safe to install a loan app?",
        "Someone is threatening to leak my video.",
        "My electricity will be cut tonight, says an SMS.",
        "How do I know if a website is fake?",
    ],
    "ta": [
        "யாரோ என் OTP கேட்கிறார்கள். நான் என்ன செய்வது?",
        "KYC காலாவதியானது என்று SMS வந்துள்ளது. இது உண்மையா?",
        "வேலை வாய்ப்பு பதிவு கட்டணம் கேட்கிறது.",
        "பணம் பெற QR ஸ்கேன் செய்ய வேண்டுமா?",
        "டிஜிட்டல் கைது என்றால் என்ன?",
        "இந்தியாவில் சைபர் மோசடியை எப்படிப் புகாரளிப்பது?",
        "கடன் செயலியை நிறுவுவது பாதுகாப்பானதா?",
        "என் வீடியோவை வெளியிடுவதாக மிரட்டுகிறார்கள்.",
        "இன்றிரவு மின்சாரம் துண்டிக்கப்படும் என்று SMS வந்துள்ளது.",
        "ஒரு இணையதளம் போலியா என எப்படி அறிவது?",
    ],
}

_URL_RE = re.compile(r"(https?://\S+|www\.\S+|\b\w+\[\.\]\w+\S*)", re.I)


def _is_refusal(question: str) -> bool:
    q = question.lower()
    return any(re.search(p, q) for p in _REFUSAL_PATTERNS)


def _looks_like_pasted_message(question: str) -> bool:
    """Heuristic: the user pasted a suspicious message rather than asking a question."""
    if len(question) < 60:
        return False
    markers = ["otp", "kyc", "click", "urgent", "blocked", "winner", "congratulations",
               "verify", "account will", "rs ", "₹", "http", "www."]
    hits = sum(m in question.lower() for m in markers)
    return hits >= 2


def _try_ollama(question: str, context: str, language: str) -> str | None:
    """Optional local LLM. Any failure returns None and the caller falls back silently."""
    if not settings.ENABLE_LLM:
        return None
    try:
        import httpx

        lang_name = "Tamil" if language == "ta" else "English"
        system = (
            f"You are a cyber-safety helper for ordinary people in India. "
            f"Answer ONLY using the provided context. Reply in {lang_name}. "
            f"Use at most 120 words and simple everyday words. "
            f"If the context does not answer the question, say you do not know and give helpline 1930. "
            f"Never invent phone numbers or website addresses."
        )
        response = httpx.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
                ],
                "stream": False,
                "options": {"temperature": 0.2},
            },
            timeout=20.0,
        )
        response.raise_for_status()
        content = response.json().get("message", {}).get("content", "").strip()
        return content or None
    except Exception as exc:
        logger.info("Ollama unavailable (%s) — using knowledge base only", type(exc).__name__)
        return None


def _article_dict(db: Session, slug: str) -> dict | None:
    """Fetch one article as a plain dict — never a detached ORM instance."""
    row = db.query(KbArticle).filter(KbArticle.slug == slug).first()
    return retriever.to_dict(row) if row else None


def _follow_ups(intent: str, slug: str | None, language: str) -> list[str]:
    """Follow-up questions that make sense after *this* answer, not a generic list."""
    ta = language == "ta"

    by_intent: dict[str, list[str]] = {
        "emergency": (
            ["1930-ல் என்ன சொல்ல வேண்டும்?", "வங்கியில் என்ன கேட்க வேண்டும்?",
             "பணம் திரும்பக் கிடைக்குமா?"]
            if ta else
            ["What do I say when I call 1930?", "What should I tell my bank?",
             "Will I get my money back?"]
        ),
        "report": (
            ["1930 என்றால் என்ன?", "என்ன ஆதாரம் தேவை?", "எவ்வளவு விரைவில் புகாரளிக்க வேண்டும்?"]
            if ta else
            ["What is 1930?", "What evidence do I need?", "How soon must I report?"]
        ),
        "helpline": (
            ["எப்படிப் புகாரளிப்பது?", "மோசடி அழைப்பை எப்படித் தடுப்பது?"]
            if ta else
            ["How do I file a report?", "How do I block a fraud number?"]
        ),
    }
    if intent in by_intent:
        return by_intent[intent]

    by_slug: dict[str, list[str]] = {
        "otp-scams": (
            ["OTP-ஐ பகிர்ந்துவிட்டேன், இப்போது என்ன?", "வங்கி உண்மையிலேயே அழைக்குமா?"]
            if ta else
            ["I already shared my OTP, what now?", "Would a real bank ever call me?"]),
        "kyc-scams": (
            ["உண்மையான KYC எப்படிச் செய்வது?", "இந்த இணைப்பு போலியா?"]
            if ta else
            ["How do I update KYC properly?", "Is this link fake?"]),
        "job-scams": (
            ["இந்த நிறுவனம் உண்மையா எனப் பார்ப்பது எப்படி?", "ஏற்கனவே கட்டணம் கட்டிவிட்டேன்"]
            if ta else
            ["How do I check if a company is real?", "I already paid the fee"]),
        "investment-scams": (
            ["SEBI பதிவை எப்படிச் சரிபார்ப்பது?", "பணத்தை எடுக்க முடியவில்லை"]
            if ta else
            ["How do I check a SEBI registration?", "I cannot withdraw my money"]),
        "upi-qr-safety": (
            ["பணம் பெற PIN தேவையா?", "QR-ஐ எப்படிச் சரிபார்ப்பது?"]
            if ta else
            ["Do I need a PIN to receive money?", "How do I check a QR code?"]),
        "loan-scams": (
            ["கடன் செயலி மிரட்டுகிறது, என்ன செய்வது?", "எங்கு புகாரளிப்பது?"]
            if ta else
            ["A loan app is threatening me, what do I do?", "Where do I report it?"]),
        "digital-arrest-scams": (
            ["இது உண்மையான காவல்துறையா எனத் தெரிவது எப்படி?", "நான் பணம் அனுப்பிவிட்டேன்"]
            if ta else
            ["How do I know if the police are real?", "I already transferred money"]),
        "social-media-scams": (
            ["என் கணக்கை எப்படி மீட்பது?", "மிரட்டுகிறார்கள், என்ன செய்வது?"]
            if ta else
            ["How do I recover my account?", "They are blackmailing me, what now?"]),
        "banking-scams": (
            ["கார்டை எப்படி முடக்குவது?", "உண்மையான கஸ்டமர் கேர் எண் எது?"]
            if ta else
            ["How do I block my card?", "What is the real customer care number?"]),
    }
    if slug and slug in by_slug:
        return by_slug[slug]

    return SUGGESTIONS[language][:3]


def ask(
    db: Session,
    question: str,
    language: str = "auto",
    simple_mode: bool = False,
    user_id: int | None = None,
) -> dict:
    detected = resolve_language(None if language == "auto" else language, question)
    redacted_q, _ = redaction.redact(question)

    def _log(source: str, article_id: int | None = None) -> int | None:
        try:
            entry = AssistantLog(
                user_id=user_id,
                language=detected,
                question_redacted=redacted_q[:1000],
                answer_source=source,
                matched_article_id=article_id,
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)
            return entry.id
        except Exception:
            db.rollback()
            logger.exception("failed to log assistant interaction")
            return None

    def _reply(
        answer: str,
        source: str,
        confidence: float,
        *,
        intent: str = "none",
        slug: str | None = None,
        related: list[dict] | None = None,
        article_id: int | None = None,
        urgent: bool = False,
    ) -> dict:
        return {
            "log_id": _log(source, article_id),
            "answer": answer,
            "language": detected,
            "source": source,
            "intent": intent,
            "confidence": round(confidence, 3),
            "urgent": urgent,
            "related_articles": related or [],
            "suggested_questions": _follow_ups(intent, slug, detected),
            "quick_actions": responses.quick_actions(
                intent if intent != "none" else source, detected
            ),
            "disclaimer": DISCLAIMER[detected],
        }

    # 1. Safety gate — before anything else.
    if _is_refusal(question):
        return _reply(REFUSAL_ANSWER[detected], "refusal", 1.0, intent="refusal")

    match = intents.detect(question)

    # 2. EMERGENCY outranks everything, including a pasted message. Someone who has just lost
    #    money needs the golden-hour steps, not an explanation of how the scam worked.
    if match.intent is Intent.EMERGENCY:
        return _reply(responses.EMERGENCY[detected], "rule", 1.0, intent="emergency", urgent=True)

    # 3. Pasted content -> the analyzers.
    url_match = _URL_RE.search(question)
    if url_match and len(question) < 300:
        result = url_service.check(db, url_match.group(0), user_id=user_id, persist=False)
        verdict = result["advice"]["ta" if detected == "ta" else "en"]
        label = result["risk_label"].replace("_", " ")
        prefix = (
            f"இந்த இணைப்பின் மதிப்பீடு: {result['risk_score']}/100 ({label}).\n\n"
            if detected == "ta"
            else f"I checked that link: {result['risk_score']}/100 ({label}).\n\n"
        )
        return _reply(
            prefix + verdict, "analyzer", 0.9,
            intent="analyzer", urgent=result["risk_label"] == "high_risk",
        )

    if _looks_like_pasted_message(question):
        result = scam_service.analyze(
            db, question, channel="sms", language=detected, user_id=user_id, persist=False
        )
        label = result["risk_label"].replace("_", " ")
        prefix = (
            f"இந்த செய்தியின் மதிப்பீடு: {result['risk_score']}/100 ({label}).\n\n"
            if detected == "ta"
            else f"I analysed that message: {result['risk_score']}/100 ({label}).\n\n"
        )
        body = result["explanation"]["ta" if detected == "ta" else "en"]
        actions = result["safe_actions"]["ta" if detected == "ta" else "en"][:3]
        answer = prefix + body + "\n\n" + "\n".join(f"• {a}" for a in actions)
        related = [
            {"slug": s, "title": s.replace("-", " ").title(), "score": 1.0}
            for s in result["related_kb_slugs"]
        ]
        return _reply(
            answer, "analyzer", 0.9, intent="analyzer",
            slug=result["related_kb_slugs"][0] if result["related_kb_slugs"] else None,
            related=related, urgent=result["risk_label"] == "high_risk",
        )

    # 4. Conversational and procedural intents that retrieval used to miss entirely.
    canned = {
        Intent.REPORT: (responses.REPORT, "report"),
        Intent.HELPLINE: (responses.HELPLINE, "helpline"),
        Intent.GREETING: (responses.GREETING, "greeting"),
        Intent.THANKS: (responses.THANKS, "thanks"),
        Intent.ABOUT: (responses.ABOUT, "about"),
    }
    if match.intent in canned:
        text, name = canned[match.intent]
        return _reply(text[detected], "rule", match.confidence, intent=name)

    # 5. Deterministic keyword route to a specific article. This is the backstop for brand and
    #    platform names ("paytm", "facebook") that never appear in the article prose.
    if match.intent is Intent.TOPIC and match.slug:
        article = _article_dict(db, match.slug)
        if article:
            answer = retriever.compose_answer(article, detected, simple_mode)
            llm = _try_ollama(
                question,
                context=(article["body_ta"] if detected == "ta" else article["body_en"])[:2500],
                language=detected,
            )
            related = [{
                "slug": article["slug"],
                "title": article["title_ta"] if detected == "ta" else article["title_en"],
                "score": match.confidence,
            }]
            return _reply(
                llm or answer, "llm" if llm else "kb", match.confidence,
                intent="topic", slug=article["slug"],
                related=related, article_id=article["id"],
            )

    # 6. KB retrieval, with the query expanded by topic keywords so a short question shares
    #    vocabulary with the article prose.
    matches = retriever.search(db, intents.expand_query(question), detected, top_k=3)
    related = [
        {
            "slug": m["article"]["slug"],
            "title": m["article"]["title_ta"] if detected == "ta" else m["article"]["title_en"],
            "score": m["score"],
        }
        for m in matches
    ]

    if matches and matches[0]["score"] >= MIN_KB_SCORE:
        best = matches[0]["article"]
        answer = retriever.compose_answer(best, detected, simple_mode)

        # 7. Optional LLM rewrite, grounded strictly in the retrieved article.
        llm = _try_ollama(
            question,
            context=(best["body_ta"] if detected == "ta" else best["body_en"])[:2500],
            language=detected,
        )
        return _reply(
            llm or answer, "llm" if llm else "kb", matches[0]["score"],
            intent="topic", slug=best["slug"], related=related, article_id=best["id"],
        )

    # 8. Honest fallback that still tells the user what I can do.
    return _reply(responses.FALLBACK[detected], "fallback", 0.0, intent="fallback", related=related)


def record_feedback(db: Session, log_id: int, helpful: bool) -> bool:
    entry = db.query(AssistantLog).filter(AssistantLog.id == log_id).first()
    if not entry:
        return False
    entry.helpful = helpful
    db.commit()
    return True


def get_suggestions(language: str = "en") -> list[str]:
    return SUGGESTIONS.get(language, SUGGESTIONS["en"])
