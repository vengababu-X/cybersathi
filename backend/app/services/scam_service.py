"""Scam message analysis: redact -> rules -> ML -> hybrid score -> bilingual explanation."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.ml import redaction, rules, text_model
from app.models import KbArticle, ScamAnalysis
from app.nlp.language import resolve_language

# Hybrid weights. Rules carry almost as much weight as the model on purpose: the model
# generalises but cannot explain itself to a non-technical user, and a brand-new scam script
# will hit a rule before it is ever in the training data.
W_ML = 0.55
W_RULES = 0.45

THRESHOLD_SUSPICIOUS = 35
THRESHOLD_HIGH = 70

DISCLAIMER = {
    "en": "Advisory only — this is an automated opinion, not a guarantee. Always verify with your bank, or call 1930.",
    "ta": "இது ஆலோசனை மட்டுமே — தானியங்கி கருத்து, உத்தரவாதம் அல்ல. உங்கள் வங்கியிடம் சரிபார்க்கவும் அல்லது 1930-ஐ அழைக்கவும்.",
}

HELPLINES = {
    "cyber_crime": "1930",
    "portal": "cybercrime.gov.in",
    "bank": "Use only the number printed on your card or passbook",
}

CATEGORY_TO_SLUG = {
    "otp": "otp-scams",
    "kyc": "kyc-scams",
    "job": "job-scams",
    "investment": "investment-scams",
    "banking": "banking-scams",
    "loan": "loan-scams",
    "impersonation": "impersonation-scams",
    "social_media": "social-media-scams",
    "digital_arrest": "digital-arrest-scams",
    "courier_parcel": "courier-parcel-scams",
    "lottery": "lottery-prize-scams",
    "electricity_bill": "impersonation-scams",
    "loan_app_harassment": "loan-scams",
}

SAFE_ACTIONS = {
    "high_risk": {
        "en": [
            "Do not reply, do not click any link, and do not call the number in the message.",
            "Never share an OTP, PIN, CVV or password with anyone.",
            "If you already shared something or paid, call 1930 right now.",
            "Verify with the official app or the number printed on your card.",
            "Tell one family member about this message today.",
        ],
        "ta": [
            "பதில் அளிக்காதீர்கள், இணைப்பை அழுத்தாதீர்கள், செய்தியில் உள்ள எண்ணை அழைக்காதீர்கள்.",
            "OTP, PIN, CVV அல்லது கடவுச்சொல்லை யாரிடமும் பகிராதீர்கள்.",
            "ஏற்கனவே ஏதாவது பகிர்ந்திருந்தால் அல்லது பணம் அனுப்பியிருந்தால் உடனே 1930-ஐ அழையுங்கள்.",
            "அதிகாரப்பூர்வ செயலி அல்லது கார்டில் உள்ள எண்ணைக் கொண்டு சரிபாருங்கள்.",
            "இந்த செய்தியைப் பற்றி இன்று ஒரு குடும்ப உறுப்பினரிடம் சொல்லுங்கள்.",
        ],
    },
    "suspicious": {
        "en": [
            "Do not act on this message until you have verified it independently.",
            "Do not open any link — type the official website address yourself.",
            "Contact the organisation using a number you already have, not one in this message.",
            "Ask a family member or friend what they think before doing anything.",
        ],
        "ta": [
            "சுயாதீனமாக சரிபார்க்கும் வரை இந்த செய்தியின்படி செயல்பட வேண்டாம்.",
            "எந்த இணைப்பையும் திறக்க வேண்டாம் — அதிகாரப்பூர்வ முகவரியை நீங்களே தட்டச்சு செய்யுங்கள்.",
            "இந்த செய்தியில் உள்ள எண் அல்ல, உங்களிடம் ஏற்கனவே உள்ள எண்ணைப் பயன்படுத்துங்கள்.",
            "எதுவும் செய்வதற்கு முன் குடும்பத்தினரிடம் கேளுங்கள்.",
        ],
    },
    "safe": {
        "en": [
            "No clear scam signals were found, but stay alert.",
            "Never share an OTP or PIN, even if a message looks genuine.",
            "If this message asks for money or details, verify it independently anyway.",
        ],
        "ta": [
            "தெளிவான மோசடி அறிகுறிகள் காணப்படவில்லை, ஆனால் எச்சரிக்கையாக இருங்கள்.",
            "செய்தி உண்மையாகத் தோன்றினாலும் OTP அல்லது PIN-ஐ பகிர வேண்டாம்.",
            "பணம் அல்லது விவரம் கேட்டால் சுயாதீனமாக சரிபாருங்கள்.",
        ],
    },
}


def _label_for(score: float) -> str:
    if score >= THRESHOLD_HIGH:
        return "high_risk"
    if score >= THRESHOLD_SUSPICIOUS:
        return "suspicious"
    return "safe"


def _build_explanation(
    label: str, category: str, hits: list[dict], language: str, pii_found: list[str]
) -> dict[str, str]:
    """Three to five short sentences at roughly an 8th-grade reading level."""
    top = [h for h in hits if h["weight"] > 0][:2]

    if label == "high_risk":
        lead_en = "This message shows strong signs of a scam."
        lead_ta = "இந்த செய்தியில் மோசடியின் வலுவான அறிகுறிகள் உள்ளன."
    elif label == "suspicious":
        lead_en = "This message has some warning signs and should be treated with caution."
        lead_ta = "இந்த செய்தியில் சில எச்சரிக்கை அறிகுறிகள் உள்ளன. கவனமாக இருங்கள்."
    else:
        lead_en = "No clear scam signals were found in this message."
        lead_ta = "இந்த செய்தியில் தெளிவான மோசடி அறிகுறிகள் இல்லை."

    en_parts = [lead_en]
    ta_parts = [lead_ta]

    for hit in top:
        en_parts.append(hit["why_en"])
        ta_parts.append(hit["why_ta"])

    if pii_found:
        en_parts.append(
            "Personal details in this message were hidden automatically before it was saved."
        )
        ta_parts.append("இந்த செய்தியில் இருந்த தனிப்பட்ட விவரங்கள் சேமிக்கும் முன் மறைக்கப்பட்டன.")

    if label != "safe":
        en_parts.append("When in doubt, do not act — call 1930 instead.")
        ta_parts.append("சந்தேகம் இருந்தால் செயல்படாதீர்கள் — 1930-ஐ அழையுங்கள்.")

    return {"en": " ".join(en_parts), "ta": " ".join(ta_parts)}


def analyze(
    db: Session,
    text: str,
    channel: str = "sms",
    language: str = "auto",
    user_id: int | None = None,
    persist: bool = True,
) -> dict:
    detected = resolve_language(None if language == "auto" else language, text)

    # Redact BEFORE anything is stored, logged or returned.
    redacted, pii_found = redaction.redact(text)

    hits = rules.evaluate(redacted, detected)
    rule_component = rules.rule_score(hits)

    ml_prob = text_model.predict_scam_probability(redacted)
    model_used = ml_prob is not None

    if model_used:
        combined = W_ML * ml_prob + W_RULES * rule_component
    else:
        combined = rule_component

    score = round(min(max(combined, 0.0), 1.0) * 100, 1)
    label = _label_for(score)

    categories = text_model.predict_category(redacted) if label != "safe" else []
    if categories:
        primary = categories[0]["name"]
    else:
        primary = rules.dominant_category(hits)

    # A near-certain rule outranks the model on category. The model is trained to generalise
    # and will happily fold a digital-arrest message into the broad "impersonation" class,
    # which would then link the user to the wrong article. For the critical, highly specific
    # scams the rule is the more precise signal.
    decisive = [
        h for h in hits
        if h["weight"] >= 0.9 and h["category"] not in {"impersonation", "banking", "legitimate"}
    ]
    if decisive and label != "safe":
        primary = max(decisive, key=lambda h: h["weight"])["category"]

    if label == "safe":
        primary = "legitimate"

    top_terms = text_model.top_contributing_terms(redacted) if model_used else []

    slug = CATEGORY_TO_SLUG.get(primary)
    related = []
    if slug:
        exists = db.query(KbArticle.slug).filter(KbArticle.slug == slug).first()
        if exists:
            related.append(slug)

    analysis_id = None
    if persist:
        record = ScamAnalysis(
            user_id=user_id,
            channel=channel,
            redacted_text=redacted[:5000],
            language=detected,
            risk_score=score,
            risk_label=label,
            primary_category=primary,
            categories_json=json.dumps(categories, ensure_ascii=False),
            matched_rules_json=json.dumps(
                [{"rule_id": h["rule_id"], "weight": h["weight"]} for h in hits],
                ensure_ascii=False,
            ),
            model_confidence=round(ml_prob, 4) if ml_prob is not None else 0.0,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        analysis_id = record.id

    return {
        "analysis_id": analysis_id,
        "risk_score": score,
        "risk_label": label,
        "primary_category": primary,
        "categories": categories,
        "language_detected": detected,
        "redacted_text": redacted,
        "pii_found": pii_found,
        "signals": [
            {
                "rule_id": h["rule_id"],
                "category": h["category"],
                "matched_snippet": h["matched_snippet"],
                "why_en": h["why_en"],
                "why_ta": h["why_ta"],
                "weight": h["weight"],
            }
            for h in sorted(hits, key=lambda x: abs(x["weight"]), reverse=True)[:6]
        ],
        "top_terms": top_terms,
        "explanation": _build_explanation(label, primary, hits, detected, pii_found),
        "safe_actions": SAFE_ACTIONS[label],
        "related_kb_slugs": related,
        "helplines": HELPLINES,
        "disclaimer": DISCLAIMER,
        "model_used": model_used,
    }
