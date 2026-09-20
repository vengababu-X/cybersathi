"""System metadata: model status, helplines, resources.

Exposing the model metrics through the API lets the frontend show real numbers on the About
page instead of hard-coded claims.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.config import settings
from app.ml import text_model, url_model

router = APIRouter(prefix="/meta", tags=["meta"])

HELPLINES = [
    {
        "name_en": "National Cyber Crime Helpline",
        "name_ta": "தேசிய சைபர் கிரைம் உதவி எண்",
        "value": "1930",
        "type": "phone",
    },
    {
        "name_en": "National Cyber Crime Reporting Portal",
        "name_ta": "தேசிய சைபர் கிரைம் புகார் தளம்",
        "value": "cybercrime.gov.in",
        "type": "url",
    },
    {
        "name_en": "Emergency",
        "name_ta": "அவசர உதவி",
        "value": "112",
        "type": "phone",
    },
    {
        "name_en": "Report fraud calls / SMS (Chakshu)",
        "name_ta": "மோசடி அழைப்பு / SMS புகார்",
        "value": "sancharsaathi.gov.in",
        "type": "url",
    },
    {
        "name_en": "Report unregistered lenders (RBI Sachet)",
        "name_ta": "பதிவு செய்யாத கடன் நிறுவனங்கள் புகார்",
        "value": "sachet.rbi.org.in",
        "type": "url",
    },
]


@router.get("/status")
def status() -> dict:
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "text_model_loaded": text_model.is_available(),
        "url_model_loaded": url_model.is_available(),
        "llm_enabled": settings.ENABLE_LLM,
        "languages": ["en", "ta"],
        "offline_capable": True,
        "api_keys_required": False,
    }


@router.get("/model-metrics")
def model_metrics() -> dict:
    """Real training metrics, plus an honest note about what they do and do not mean."""
    return {
        "text_model": text_model.get_metadata(),
        "url_model": url_model.get_metadata(),
        "interpretation_note": (
            "These scores are measured on held-out data drawn from the same synthetic corpus "
            "used for training. Because that corpus is template-generated, the classes are more "
            "cleanly separable than real-world traffic, so these figures represent an upper "
            "bound and not expected field accuracy. See docs/ML_METRICS.md."
        ),
    }


@router.get("/helplines")
def helplines() -> list[dict]:
    return HELPLINES
