"""Inference wrapper for the phishing-URL model."""

from __future__ import annotations

import json
import logging
import threading

import joblib

from app.config import ARTIFACT_DIR
from app.ml.features import FEATURE_NAMES, detect_lookalike_brand, extract_url_features

logger = logging.getLogger(__name__)

_MODEL_PATH = ARTIFACT_DIR / "url_model.joblib"
_META_PATH = ARTIFACT_DIR / "url_model_meta.json"

_bundle: dict | None = None
_meta: dict | None = None
_lock = threading.Lock()
_load_attempted = False

# Plain-language reasons. Keyed by feature name so the UI never shows a raw feature label.
REASON_TEXT: dict[str, dict[str, str]] = {
    "has_ip_host": {
        "en": "The address is a bare IP number instead of a website name. Real banks never do this.",
        "ta": "இணைய முகவரிக்கு பதிலாக IP எண் உள்ளது. உண்மையான வங்கிகள் இப்படி செய்வதில்லை.",
    },
    "suspicious_tld": {
        "en": "The website ends in an unusual, cheap domain extension that scammers buy in bulk.",
        "ta": "இந்த தளம் மோசடியாளர்கள் மலிவாக வாங்கும் அசாதாரண டொமைன் முடிவைக் கொண்டுள்ளது.",
    },
    "shortener_flag": {
        "en": "This is a shortened link, so the real destination is hidden from you.",
        "ta": "இது சுருக்கப்பட்ட இணைப்பு. உண்மையான முகவரி உங்களிடமிருந்து மறைக்கப்படுகிறது.",
    },
    "is_typosquat": {
        "en": "The name is a near-copy of a well-known brand with letters changed or swapped.",
        "ta": "பிரபலமான நிறுவனத்தின் பெயரை எழுத்துக்களை மாற்றி நகலெடுத்துள்ளார்கள்.",
    },
    "has_at_symbol": {
        "en": "The address contains '@', a trick that makes the visible part differ from the real site.",
        "ta": "முகவரியில் '@' உள்ளது. இது தெரியும் பகுதிக்கும் உண்மையான தளத்திற்கும் வேறுபாடு உருவாக்கும் தந்திரம்.",
    },
    "has_punycode": {
        "en": "The address uses look-alike foreign characters to imitate a real name.",
        "ta": "உண்மையான பெயரை பின்பற்ற வேற்று எழுத்துக்கள் பயன்படுத்தப்பட்டுள்ளன.",
    },
    "sensitive_word_hit": {
        "en": "The link contains words like login, verify or KYC that are used to rush you into typing details.",
        "ta": "இணைப்பில் login, verify, KYC போன்ற சொற்கள் உள்ளன. இவை அவசரமாக விவரங்களை உள்ளிட வைக்க பயன்படுகின்றன.",
    },
    "brand_keyword_hit": {
        "en": "A bank or company name appears in the address, but not as the official domain.",
        "ta": "வங்கி அல்லது நிறுவனத்தின் பெயர் முகவரியில் உள்ளது, ஆனால் அது அதிகாரப்பூர்வ தளம் அல்ல.",
    },
    "num_hyphens": {
        "en": "The address has many hyphens, commonly used to stitch together a fake brand name.",
        "ta": "முகவரியில் பல ஹைஃபன்கள் உள்ளன. போலி பெயரை உருவாக்க இது பயன்படுகிறது.",
    },
    "hyphen_in_domain": {
        "en": "The main domain contains a hyphen, which official Indian bank sites rarely use.",
        "ta": "முக்கிய டொமைனில் ஹைஃபன் உள்ளது. அதிகாரப்பூர்வ வங்கி தளங்களில் இது அரிது.",
    },
    "num_subdomains": {
        "en": "The address has many parts before the real domain, hiding where it actually goes.",
        "ta": "உண்மையான டொமைனுக்கு முன் பல பகுதிகள் உள்ளன. இது இலக்கை மறைக்கிறது.",
    },
    "digit_ratio": {
        "en": "The address contains an unusual number of digits for a genuine site.",
        "ta": "உண்மையான தளத்திற்கு இருக்கக்கூடாத அளவுக்கு எண்கள் உள்ளன.",
    },
    "url_length": {
        "en": "The address is very long, which is often used to push the real domain out of view on a phone.",
        "ta": "முகவரி மிக நீளமானது. ஃபோனில் உண்மையான டொமைன் தெரியாமல் மறைக்க இது பயன்படுகிறது.",
    },
    "is_https": {
        "en": "Note: a padlock or 'https' does NOT mean a site is safe — scam sites get free certificates too.",
        "ta": "கவனிக்க: பூட்டு சின்னம் அல்லது 'https' பாதுகாப்பானது என்று அர்த்தம் இல்லை — மோசடி தளங்களும் இலவசமாக பெறுகின்றன.",
    },
    "host_entropy": {
        "en": "The domain looks like random characters rather than a real word.",
        "ta": "டொமைன் ஒரு உண்மையான சொல் போல் இல்லாமல் தற்செயலான எழுத்துக்களாக உள்ளது.",
    },
}


def _load() -> dict | None:
    global _bundle, _meta, _load_attempted
    if _bundle is not None:
        return _bundle
    with _lock:
        if _bundle is not None:
            return _bundle
        if _load_attempted and _bundle is None:
            return None
        _load_attempted = True
        if not _MODEL_PATH.exists():
            logger.warning("url model not found at %s — heuristics only", _MODEL_PATH)
            return None
        try:
            _bundle = joblib.load(_MODEL_PATH)
            if _META_PATH.exists():
                _meta = json.loads(_META_PATH.read_text(encoding="utf-8"))
            logger.info("url model loaded")
        except Exception:
            logger.exception("failed to load url model")
            _bundle = None
        return _bundle


def is_available() -> bool:
    return _load() is not None


def get_metadata() -> dict:
    _load()
    return _meta or {}


def predict_phishing_probability(url: str) -> float | None:
    bundle = _load()
    if not bundle:
        return None
    try:
        feats = extract_url_features(url)
        vector = [[feats[name] for name in bundle["feature_names"]]]
        model = bundle["model"]
        classes = list(model.classes_)
        proba = model.predict_proba(vector)[0]
        return float(proba[classes.index("phishing")])
    except Exception:
        logger.exception("url prediction failed")
        return None


def heuristic_probability(feats: dict[str, float]) -> float:
    """Fallback scoring when no trained model is present.

    Deliberately conservative: it is better for the app to say 'suspicious' and make the user
    check, than to say 'safe' about something it cannot actually assess.
    """
    score = 0.0
    if feats["has_ip_host"]:
        score += 0.45
    if feats["has_at_symbol"]:
        score += 0.30
    if feats["has_punycode"]:
        score += 0.30
    if feats["is_typosquat"]:
        score += 0.35
    if feats["suspicious_tld"]:
        score += 0.25
    if feats["shortener_flag"]:
        score += 0.20
    if feats["hyphen_in_domain"] and feats["brand_keyword_hit"]:
        score += 0.25
    if feats["sensitive_word_hit"] >= 2:
        score += 0.15
    if feats["num_subdomains"] >= 3:
        score += 0.15
    if feats["url_length"] > 90:
        score += 0.10
    return min(score, 0.99)


def explain(url: str, top_k: int = 5) -> list[dict]:
    """Human-readable reasons, ordered by how much each feature matters in the trained model."""
    feats = extract_url_features(url)
    bundle = _load()
    lookalike = detect_lookalike_brand(url)

    importances: dict[str, float] = {}
    if bundle:
        # Saved together, so the name list and the importance vector always match; strict=True
        # turns a corrupted artifact into a loud failure instead of a silent mislabelling.
        importances = dict(
            zip(bundle["feature_names"], bundle["model"].feature_importances_, strict=True)
        )

    triggered: list[tuple[str, float, float]] = []
    for name in FEATURE_NAMES:
        value = feats.get(name, 0.0)
        fired = False
        if name in {"has_ip_host", "has_at_symbol", "has_punycode", "is_typosquat",
                    "suspicious_tld", "shortener_flag", "hyphen_in_domain"}:
            fired = value > 0
        elif name == "sensitive_word_hit":
            fired = value >= 1
        elif name == "num_subdomains":
            fired = value >= 3
        elif name == "num_hyphens":
            fired = value >= 2
        elif name == "url_length":
            fired = value > 90
        elif name == "digit_ratio":
            fired = value > 0.12
        elif name == "host_entropy":
            fired = value > 3.6
        elif name == "brand_keyword_hit":
            # Only a concern when the URL is actually impersonating the brand. On the genuine
            # bank site this reason would tell the user their real bank looks fake, which is
            # worse than saying nothing.
            fired = value > 0 and lookalike is not None
        if fired and name in REASON_TEXT:
            triggered.append((name, value, importances.get(name, 0.01)))

    triggered.sort(key=lambda t: t[2], reverse=True)

    reasons = [
        {
            "feature": name,
            "value": value,
            "why_en": REASON_TEXT[name]["en"],
            "why_ta": REASON_TEXT[name]["ta"],
        }
        for name, value, _ in triggered[:top_k]
    ]

    # Always counter the padlock myth on an HTTPS URL that still looks risky.
    if feats["is_https"] and reasons:
        reasons.append(
            {
                "feature": "is_https",
                "value": 1.0,
                "why_en": REASON_TEXT["is_https"]["en"],
                "why_ta": REASON_TEXT["is_https"]["ta"],
            }
        )
    return reasons
