"""Knowledge base and assistant endpoints."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.deps import get_optional_user, rate_limit
from app.database import get_db
from app.models import KbArticle, User
from app.schemas import (
    AssistantAskRequest,
    AssistantAskResponse,
    AssistantFeedback,
    BilingualList,
    KbArticleDetail,
    KbArticleSummary,
    KbCategory,
)
from app.services import assistant_service

router = APIRouter(tags=["knowledge"])

CATEGORY_LABELS = {
    "otp": ("OTP Scams", "OTP மோசடி"),
    "kyc": ("KYC Scams", "KYC மோசடி"),
    "job": ("Job Scams", "வேலை மோசடி"),
    "investment": ("Investment Scams", "முதலீட்டு மோசடி"),
    "banking": ("Banking Frauds", "வங்கி மோசடி"),
    "loan": ("Loan Scams", "கடன் மோசடி"),
    "impersonation": ("Impersonation", "ஆள்மாறாட்டம்"),
    "social_media": ("Social Media Scams", "சமூக ஊடக மோசடி"),
    "digital_arrest": ("Digital Arrest", "டிஜிட்டல் கைது"),
    "courier_parcel": ("Courier & Parcel", "கூரியர் மோசடி"),
    "lottery": ("Lottery & Prizes", "லாட்டரி மோசடி"),
    "loan_app_harassment": ("Loan App Harassment", "கடன் செயலி மிரட்டல்"),
}


def _to_detail(article: KbArticle) -> KbArticleDetail:
    def _bilingual(raw: str) -> BilingualList:
        try:
            data = json.loads(raw or "{}")
        except json.JSONDecodeError:
            data = {}
        return BilingualList(en=data.get("en", []), ta=data.get("ta", []))

    return KbArticleDetail(
        id=article.id,
        slug=article.slug,
        category=article.category,
        severity=article.severity,
        title_en=article.title_en,
        title_ta=article.title_ta,
        summary_en=article.summary_en,
        summary_ta=article.summary_ta,
        helpline=article.helpline,
        views=article.views,
        body_en=article.body_en,
        body_ta=article.body_ta,
        red_flags=_bilingual(article.red_flags_json),
        safe_actions=_bilingual(article.safe_actions_json),
        victim_steps=_bilingual(article.victim_steps_json),
        real_example_en=article.real_example_en,
        real_example_ta=article.real_example_ta,
        tags=article.tags,
    )


@router.get("/kb/articles", response_model=list[KbArticleSummary])
def list_articles(
    category: str | None = Query(default=None),
    q: str | None = Query(default=None, max_length=200),
    db: Session = Depends(get_db),
) -> list[KbArticleSummary]:
    query = db.query(KbArticle)
    if category:
        query = query.filter(KbArticle.category == category)
    if q:
        like = f"%{q}%"
        # Search both languages at once: a user may type Tamil while the UI is in English.
        query = query.filter(
            or_(
                KbArticle.title_en.ilike(like),
                KbArticle.title_ta.ilike(like),
                KbArticle.summary_en.ilike(like),
                KbArticle.summary_ta.ilike(like),
                KbArticle.tags.ilike(like),
            )
        )
    return [KbArticleSummary.model_validate(a) for a in query.all()]


@router.get("/kb/categories", response_model=list[KbCategory])
def list_categories(db: Session = Depends(get_db)) -> list[KbCategory]:
    from sqlalchemy import func

    rows = (
        db.query(KbArticle.category, func.count(KbArticle.id))
        .group_by(KbArticle.category)
        .all()
    )
    out = []
    for category, count in rows:
        label_en, label_ta = CATEGORY_LABELS.get(category, (category.title(), category.title()))
        out.append(
            KbCategory(category=category, count=count, label_en=label_en, label_ta=label_ta)
        )
    return sorted(out, key=lambda c: c.category)


@router.get("/kb/articles/{slug}", response_model=KbArticleDetail)
def get_article(slug: str, db: Session = Depends(get_db)) -> KbArticleDetail:
    article = db.query(KbArticle).filter(KbArticle.slug == slug).first()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article not found")
    article.views += 1
    db.commit()
    db.refresh(article)
    return _to_detail(article)


# ---------------------------------------------------------------------- assistant
@router.post("/assistant/ask", response_model=AssistantAskResponse)
def ask_assistant(
    payload: AssistantAskRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
    _: None = Depends(rate_limit),
) -> AssistantAskResponse:
    result = assistant_service.ask(
        db,
        question=payload.question,
        language=payload.language,
        simple_mode=payload.simple_mode,
        user_id=user.id if user else None,
    )
    return AssistantAskResponse(**result)


@router.post("/assistant/feedback", status_code=status.HTTP_204_NO_CONTENT)
def assistant_feedback(payload: AssistantFeedback, db: Session = Depends(get_db)) -> None:
    ok = assistant_service.record_feedback(db, payload.log_id, payload.helpful)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log entry not found")


@router.get("/assistant/suggestions", response_model=list[str])
def assistant_suggestions(language: str = Query(default="en", pattern="^(en|ta)$")) -> list[str]:
    return assistant_service.get_suggestions(language)
