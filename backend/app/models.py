"""ORM models.

Privacy note: no table stores raw OTPs, card numbers, Aadhaar, passwords in plain text, or
raw phone numbers. Analysed text is redacted before it reaches the database, and participant
phone numbers are stored only as a salted SHA-256 hash.
"""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="participant")  # admin|volunteer|participant
    preferred_language: Mapped[str] = mapped_column(String(5), default="en")
    age_group: Mapped[str | None] = mapped_column(String(20), nullable=True)
    locality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    workshops: Mapped[list["Workshop"]] = relationship(back_populates="facilitator")


class Workshop(Base):
    __tablename__ = "workshops"

    id: Mapped[int] = mapped_column(primary_key=True)
    title_en: Mapped[str] = mapped_column(String(200))
    title_ta: Mapped[str] = mapped_column(String(200))
    venue: Mapped[str] = mapped_column(String(200))
    locality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    district: Mapped[str] = mapped_column(String(120), index=True)
    conducted_on: Mapped[datetime] = mapped_column(Date, index=True)
    facilitator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    audience_type: Mapped[str] = mapped_column(String(40))  # school|college|senior|rural|women|mixed
    participants_expected: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    facilitator: Mapped["User | None"] = relationship(back_populates="workshops")
    participants: Mapped[list["Participant"]] = relationship(
        back_populates="workshop", cascade="all, delete-orphan"
    )


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(primary_key=True)
    workshop_id: Mapped[int] = mapped_column(ForeignKey("workshops.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    age_group: Mapped[str] = mapped_column(String(20))  # student|adult|senior
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    language: Mapped[str] = mapped_column(String(5), default="en")
    # SHA-256 hash only — the raw number is never persisted.
    phone_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    consent_given: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    workshop: Mapped["Workshop"] = relationship(back_populates="participants")
    assessments: Mapped[list["Assessment"]] = relationship(
        back_populates="participant", cascade="all, delete-orphan"
    )


class Assessment(Base):
    __tablename__ = "assessments"
    __table_args__ = (
        UniqueConstraint("participant_id", "type", name="uq_participant_assessment_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    participant_id: Mapped[int] = mapped_column(ForeignKey("participants.id"), index=True)
    workshop_id: Mapped[int] = mapped_column(ForeignKey("workshops.id"), index=True)
    type: Mapped[str] = mapped_column(String(10))  # pre|post
    score: Mapped[int] = mapped_column(Integer)
    max_score: Mapped[int] = mapped_column(Integer)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    answers_json: Mapped[str] = mapped_column(Text, default="[]")
    taken_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    participant: Mapped["Participant"] = relationship(back_populates="assessments")


class ScamAnalysis(Base):
    __tablename__ = "scam_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(20))
    redacted_text: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(5))
    risk_score: Mapped[float] = mapped_column(Float)
    risk_label: Mapped[str] = mapped_column(String(20), index=True)
    primary_category: Mapped[str] = mapped_column(String(40), index=True)
    categories_json: Mapped[str] = mapped_column(Text, default="[]")
    matched_rules_json: Mapped[str] = mapped_column(Text, default="[]")
    model_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class UrlCheck(Base):
    __tablename__ = "url_checks"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    submitted_url_redacted: Mapped[str] = mapped_column(String(600))
    risk_score: Mapped[float] = mapped_column(Float)
    risk_label: Mapped[str] = mapped_column(String(20), index=True)
    features_json: Mapped[str] = mapped_column(Text, default="{}")
    top_reasons_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class KbArticle(Base):
    __tablename__ = "kb_articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    severity: Mapped[str] = mapped_column(String(20), default="high")
    title_en: Mapped[str] = mapped_column(String(200))
    title_ta: Mapped[str] = mapped_column(String(200))
    summary_en: Mapped[str] = mapped_column(Text)
    summary_ta: Mapped[str] = mapped_column(Text)
    body_en: Mapped[str] = mapped_column(Text)
    body_ta: Mapped[str] = mapped_column(Text)
    red_flags_json: Mapped[str] = mapped_column(Text, default="{}")
    safe_actions_json: Mapped[str] = mapped_column(Text, default="{}")
    victim_steps_json: Mapped[str] = mapped_column(Text, default="{}")
    real_example_en: Mapped[str] = mapped_column(Text, default="")
    real_example_ta: Mapped[str] = mapped_column(Text, default="")
    helpline: Mapped[str] = mapped_column(String(120), default="1930")
    tags: Mapped[str] = mapped_column(String(300), default="")
    views: Mapped[int] = mapped_column(Integer, default=0)


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    difficulty: Mapped[str] = mapped_column(String(10), default="easy")
    question_en: Mapped[str] = mapped_column(Text)
    question_ta: Mapped[str] = mapped_column(Text)
    options_en_json: Mapped[str] = mapped_column(Text)
    options_ta_json: Mapped[str] = mapped_column(Text)
    correct_index: Mapped[int] = mapped_column(Integer)
    explanation_en: Mapped[str] = mapped_column(Text)
    explanation_ta: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class AssistantLog(Base):
    __tablename__ = "assistant_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    language: Mapped[str] = mapped_column(String(5))
    question_redacted: Mapped[str] = mapped_column(Text)
    answer_source: Mapped[str] = mapped_column(String(20))  # rule|kb|llm|fallback|refusal
    matched_article_id: Mapped[int | None] = mapped_column(
        ForeignKey("kb_articles.id"), nullable=True
    )
    helpful: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class FeedbackEntry(Base):
    __tablename__ = "feedback_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    workshop_id: Mapped[int] = mapped_column(ForeignKey("workshops.id"), index=True)
    participant_id: Mapped[int | None] = mapped_column(ForeignKey("participants.id"), nullable=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


Index("ix_scam_created_label", ScamAnalysis.created_at, ScamAnalysis.risk_label)
Index("ix_assessment_workshop_type", Assessment.workshop_id, Assessment.type)
