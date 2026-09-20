"""Workshops, participants, assessments, dashboard and exports."""

from __future__ import annotations

import csv
import io
import json
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.database import get_db
from app.ml.redaction import hash_phone
from app.models import Assessment, FeedbackEntry, Participant, User, Workshop
from app.schemas import (
    AssessmentResult,
    AssessmentSubmit,
    DashboardSummary,
    FeedbackCreate,
    ImprovementResult,
    ParticipantCreate,
    ParticipantOut,
    QuizOption,
    QuizQuestionOut,
    WorkshopCreate,
    WorkshopOut,
)
from app.services import assessment_service, dashboard_service

router = APIRouter(tags=["community"])


# ---------------------------------------------------------------------- workshops
@router.post("/workshops", response_model=WorkshopOut, status_code=status.HTTP_201_CREATED)
def create_workshop(
    payload: WorkshopCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "volunteer")),
) -> WorkshopOut:
    workshop = Workshop(**payload.model_dump(), facilitator_id=user.id)
    db.add(workshop)
    db.commit()
    db.refresh(workshop)
    return WorkshopOut.model_validate(workshop)


@router.get("/workshops", response_model=list[WorkshopOut])
def list_workshops(
    district: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
) -> list[WorkshopOut]:
    query = db.query(Workshop)
    if district:
        query = query.filter(Workshop.district == district)
    if date_from:
        query = query.filter(Workshop.conducted_on >= date_from)
    if date_to:
        query = query.filter(Workshop.conducted_on <= date_to)
    return [
        WorkshopOut.model_validate(w)
        for w in query.order_by(Workshop.conducted_on.desc()).all()
    ]


@router.post(
    "/workshops/{workshop_id}/participants",
    response_model=list[ParticipantOut],
    status_code=status.HTTP_201_CREATED,
)
def add_participants(
    workshop_id: int,
    payload: list[ParticipantCreate],
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "volunteer")),
) -> list[ParticipantOut]:
    workshop = db.query(Workshop).filter(Workshop.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workshop not found")

    created = []
    for item in payload:
        participant = Participant(
            workshop_id=workshop_id,
            name=item.name,
            age_group=item.age_group,
            gender=item.gender,
            language=item.language,
            # The raw phone number is hashed here and never stored.
            phone_hash=hash_phone(item.phone) if item.phone else None,
            consent_given=item.consent_given,
        )
        db.add(participant)
        created.append(participant)

    db.commit()
    for p in created:
        db.refresh(p)
    return [ParticipantOut.model_validate(p) for p in created]


@router.get("/workshops/{workshop_id}/participants", response_model=list[ParticipantOut])
def list_participants(workshop_id: int, db: Session = Depends(get_db)) -> list[ParticipantOut]:
    rows = db.query(Participant).filter(Participant.workshop_id == workshop_id).all()
    return [ParticipantOut.model_validate(p) for p in rows]


# --------------------------------------------------------------------- assessment
@router.get("/assessment/questions", response_model=list[QuizQuestionOut])
def get_questions(
    workshop_id: int,
    participant_id: int,
    type: str = Query(pattern="^(pre|post)$"),
    language: str = Query(default="en", pattern="^(en|ta)$"),
    count: int = Query(default=10, ge=1, le=25),
    db: Session = Depends(get_db),
) -> list[QuizQuestionOut]:
    questions = assessment_service.select_questions(
        db, workshop_id, participant_id, type, count
    )
    out = []
    for q in questions:
        options = json.loads(q.options_ta_json if language == "ta" else q.options_en_json)
        out.append(
            QuizQuestionOut(
                id=q.id,
                category=q.category,
                difficulty=q.difficulty,
                question=q.question_ta if language == "ta" else q.question_en,
                options=[QuizOption(index=i, text=t) for i, t in enumerate(options)],
            )
        )
    return out


@router.post("/assessment/submit", response_model=AssessmentResult)
def submit_assessment(
    payload: AssessmentSubmit, db: Session = Depends(get_db)
) -> AssessmentResult:
    participant = db.query(Participant).filter(Participant.id == payload.participant_id).first()
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")

    result = assessment_service.submit(
        db,
        participant_id=payload.participant_id,
        workshop_id=payload.workshop_id,
        assessment_type=payload.type,
        answers=[a.model_dump() for a in payload.answers],
        duration_seconds=payload.duration_seconds,
        language=payload.language,
    )
    return AssessmentResult(**result)


@router.get(
    "/assessment/participant/{participant_id}/improvement", response_model=ImprovementResult
)
def participant_improvement(
    participant_id: int, db: Session = Depends(get_db)
) -> ImprovementResult:
    result = assessment_service.improvement_for_participant(db, participant_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")
    return ImprovementResult(**result)


# ---------------------------------------------------------------------- dashboard
@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    date_from: date | None = None,
    date_to: date | None = None,
    district: str | None = None,
    audience: str | None = None,
    db: Session = Depends(get_db),
) -> DashboardSummary:
    return DashboardSummary(
        **dashboard_service.summary(db, date_from, date_to, district, audience)
    )


@router.get("/dashboard/export")
def export_report(
    format: str = Query(default="csv", pattern="^(csv|json|pdf)$"),
    date_from: date | None = None,
    date_to: date | None = None,
    district: str | None = None,
    audience: str | None = None,
    db: Session = Depends(get_db),
) -> Response:
    rows = dashboard_service.export_rows(db)

    if format == "pdf":
        # The printable artefact for the Community Service Project appendix: the statistics
        # and their caveats on the same page, so the mean is never quoted bare.
        from app.services.report_service import build_impact_report

        summary = dashboard_service.summary(db, date_from, date_to, district, audience)
        pdf = build_impact_report(summary, rows)
        return Response(
            content=pdf,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=cybersathi_impact_report.pdf"},
        )

    if format == "json":
        return Response(
            content=json.dumps(rows, indent=2, default=str),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=cybersathi_impact.json"},
        )

    buffer = io.StringIO()
    if rows:
        writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    else:
        buffer.write("no_paired_assessments_yet\n")

    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=cybersathi_impact.csv"},
    )


# ----------------------------------------------------------------------- feedback
@router.post("/feedback", status_code=status.HTTP_201_CREATED)
def create_feedback(payload: FeedbackCreate, db: Session = Depends(get_db)) -> dict:
    entry = FeedbackEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"id": entry.id, "status": "recorded"}


# --------------------------------------------------------------------- certificate
@router.get("/certificates/{participant_id}")
def certificate(participant_id: int, db: Session = Depends(get_db)) -> Response:
    """Bilingual PDF certificate. Issued only after the post-test is complete."""
    from app.services.certificate_service import build_certificate

    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Participant not found")

    post = (
        db.query(Assessment)
        .filter(Assessment.participant_id == participant_id, Assessment.type == "post")
        .first()
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Certificate is available only after the post-test is completed",
        )

    result = assessment_service.improvement_for_participant(db, participant_id)
    workshop = db.query(Workshop).filter(Workshop.id == participant.workshop_id).first()
    pdf = build_certificate(participant, workshop, result or {})

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=cybersathi_certificate_{participant_id}.pdf"
        },
    )
