"""Scam analyzer, URL checker and QR/UPI safety endpoints."""

from __future__ import annotations

import csv
import random
from pathlib import Path

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.config import DATA_DIR
from app.core.deps import get_optional_user, rate_limit
from app.database import get_db
from app.models import User
from app.schemas import (
    QrAnalyzeRequest,
    QrAnalyzeResponse,
    ScamAnalyzeRequest,
    ScamAnalyzeResponse,
    ScamExample,
    Scenario,
    UrlBulkRequest,
    UrlCheckRequest,
    UrlCheckResponse,
)
from app.services import qr_service, scam_service, url_service

router = APIRouter(tags=["detection"])


@router.post("/scam/analyze", response_model=ScamAnalyzeResponse)
def analyze_scam(
    payload: ScamAnalyzeRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
    _: None = Depends(rate_limit),
) -> ScamAnalyzeResponse:
    result = scam_service.analyze(
        db,
        text=payload.text,
        channel=payload.channel,
        language=payload.language,
        user_id=user.id if user else None,
    )
    return ScamAnalyzeResponse(**result)


@router.post("/url/check", response_model=UrlCheckResponse)
def check_url(
    payload: UrlCheckRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
    _: None = Depends(rate_limit),
) -> UrlCheckResponse:
    result = url_service.check(db, payload.url, user_id=user.id if user else None)
    return UrlCheckResponse(**result)


@router.post("/url/bulk-check", response_model=list[UrlCheckResponse])
def bulk_check_urls(
    payload: UrlBulkRequest,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
    _: None = Depends(rate_limit),
) -> list[UrlCheckResponse]:
    results = url_service.check_bulk(db, payload.urls, user_id=user.id if user else None)
    return [UrlCheckResponse(**r) for r in results]


@router.post("/qr/analyze", response_model=QrAnalyzeResponse)
def analyze_qr(
    payload: QrAnalyzeRequest, _: None = Depends(rate_limit)
) -> QrAnalyzeResponse:
    return QrAnalyzeResponse(**qr_service.analyze_payload(payload.payload))


@router.get("/qr/scenarios", response_model=list[Scenario])
def qr_scenarios() -> list[Scenario]:
    return [Scenario(**s) for s in qr_service.get_scenarios()]


_examples_cache: list[dict] | None = None


def _load_examples() -> list[dict]:
    """Curated demo samples so a facilitator never has to type a real scam message on stage."""
    global _examples_cache
    if _examples_cache is not None:
        return _examples_cache

    path: Path = DATA_DIR / "scam_messages.csv"
    rows: list[dict] = []
    if path.exists():
        with path.open(encoding="utf-8") as f:
            for i, row in enumerate(csv.DictReader(f)):
                rows.append(
                    {
                        "id": i,
                        "category": row.get("category", "unknown"),
                        "language": row.get("language", "en"),
                        "text": row.get("text", ""),
                        "label": row.get("label", "scam"),
                    }
                )

    # Two per category keeps the demo list short and varied.
    rng = random.Random(7)
    by_category: dict[str, list[dict]] = {}
    for r in rows:
        by_category.setdefault(f"{r['category']}_{r['language']}", []).append(r)

    selected: list[dict] = []
    for key in sorted(by_category):
        pool = by_category[key]
        selected.extend(rng.sample(pool, min(2, len(pool))))

    _examples_cache = selected
    return selected


@router.get("/scam/examples", response_model=list[ScamExample])
def scam_examples(
    category: str | None = Query(default=None),
    language: str | None = Query(default=None),
) -> list[ScamExample]:
    examples = _load_examples()
    if category:
        examples = [e for e in examples if e["category"] == category]
    if language:
        examples = [e for e in examples if e["language"] == language]
    return [ScamExample(**e) for e in examples[:40]]
