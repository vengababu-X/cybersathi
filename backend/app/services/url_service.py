"""Phishing URL checking. Static analysis only — the URL is never fetched."""

from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.ml import url_model
from app.ml.features import detect_lookalike_brand, extract_url_features, normalise_url
from app.ml.redaction import defang_url, undefang_url
from app.models import UrlCheck

THRESHOLD_SUSPICIOUS = 35
THRESHOLD_HIGH = 70

DISCLAIMER = {
    "en": "Advisory only — based on the address text alone. We never open the link. A 'safe' result is not a guarantee.",
    "ta": "ஆலோசனை மட்டுமே — முகவரியின் எழுத்தை மட்டும் வைத்து மதிப்பிடப்பட்டது. நாங்கள் இணைப்பைத் திறப்பதில்லை. 'பாதுகாப்பானது' என்பது உத்தரவாதம் அல்ல.",
}


def _label_for(score: float) -> str:
    if score >= THRESHOLD_HIGH:
        return "high_risk"
    if score >= THRESHOLD_SUSPICIOUS:
        return "suspicious"
    return "safe"


def _advice(label: str, brand: str | None) -> dict[str, str]:
    if label == "high_risk":
        en = "Do not open this link. It shows several signs of a fake website built to steal your details."
        ta = "இந்த இணைப்பைத் திறக்காதீர்கள். உங்கள் விவரங்களைத் திருட உருவாக்கப்பட்ட போலி தளத்தின் அறிகுறிகள் உள்ளன."
    elif label == "suspicious":
        en = "Be careful with this link. Do not enter any personal or banking details on it."
        ta = "இந்த இணைப்பில் கவனமாக இருங்கள். தனிப்பட்ட அல்லது வங்கி விவரங்களை உள்ளிட வேண்டாம்."
    else:
        en = "No strong warning signs were found in this address, but still avoid entering details if you reached it from an unexpected message."
        ta = "இந்த முகவரியில் வலுவான எச்சரிக்கை அறிகுறிகள் இல்லை. இருப்பினும் எதிர்பாராத செய்தியிலிருந்து வந்திருந்தால் விவரங்களை உள்ளிட வேண்டாம்."

    if brand:
        en += f" It appears to imitate {brand}. Open the official {brand} app or type the real address yourself instead."
        ta += f" இது {brand} நிறுவனத்தைப் போல் நடிக்கிறது. அதிகாரப்பூர்வ செயலியைத் திறங்கள் அல்லது உண்மையான முகவரியை நீங்களே தட்டச்சு செய்யுங்கள்."

    return {"en": en, "ta": ta}


def check(db: Session, raw_url: str, user_id: int | None = None, persist: bool = True) -> dict:
    # Accept defanged input so facilitators can paste straight from awareness material.
    url = normalise_url(undefang_url(raw_url))
    feats = extract_url_features(url)

    prob = url_model.predict_phishing_probability(url)
    model_used = prob is not None
    if prob is None:
        prob = url_model.heuristic_probability(feats)

    score = round(prob * 100, 1)
    label = _label_for(score)
    brand = detect_lookalike_brand(url)

    # A confirmed brand impersonation should never be reported as merely 'suspicious'.
    if brand and label == "suspicious":
        score = max(score, float(THRESHOLD_HIGH))
        label = "high_risk"

    reasons = url_model.explain(url)
    defanged = defang_url(url)

    check_id = None
    if persist:
        record = UrlCheck(
            user_id=user_id,
            submitted_url_redacted=defanged[:600],
            risk_score=score,
            risk_label=label,
            features_json=json.dumps(feats),
            top_reasons_json=json.dumps(reasons, ensure_ascii=False),
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        check_id = record.id

    return {
        "check_id": check_id,
        "url_defanged": defanged,
        "risk_score": score,
        "risk_label": label,
        "features": feats,
        "top_reasons": reasons,
        "lookalike_brand": brand,
        "advice": _advice(label, brand),
        "disclaimer": DISCLAIMER,
        "model_used": model_used,
    }


def check_bulk(db: Session, urls: list[str], user_id: int | None = None) -> list[dict]:
    return [check(db, u, user_id=user_id, persist=False) for u in urls[:20]]
