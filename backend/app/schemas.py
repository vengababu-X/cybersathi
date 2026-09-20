"""Pydantic request/response models."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

Language = Literal["en", "ta"]
LanguageOrAuto = Literal["en", "ta", "auto"]
RiskLabel = Literal["safe", "suspicious", "high_risk"]


# ----------------------------------------------------------------------------- auth
class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: Literal["admin", "volunteer", "participant"] = "participant"
    preferred_language: Language = "en"
    age_group: Literal["student", "adult", "senior"] | None = None
    locality: str | None = None


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: EmailStr
    role: str
    preferred_language: str
    age_group: str | None = None
    locality: str | None = None
    is_active: bool = True
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class RoleChange(BaseModel):
    role: Literal["admin", "volunteer", "participant"]


class ActiveChange(BaseModel):
    is_active: bool


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=6, max_length=128)


# ------------------------------------------------------------------- scam analysis
class ScamAnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    channel: Literal["sms", "whatsapp", "email", "call_transcript"] = "sms"
    language: LanguageOrAuto = "auto"


class Signal(BaseModel):
    rule_id: str
    category: str
    matched_snippet: str
    why_en: str
    why_ta: str
    weight: float


class CategoryScore(BaseModel):
    name: str
    confidence: float


class TermContribution(BaseModel):
    term: str
    contribution: float


class BilingualText(BaseModel):
    en: str
    ta: str


class BilingualList(BaseModel):
    en: list[str]
    ta: list[str]


class ScamAnalyzeResponse(BaseModel):
    analysis_id: int | None
    risk_score: float
    risk_label: RiskLabel
    primary_category: str
    categories: list[CategoryScore]
    language_detected: str
    redacted_text: str
    pii_found: list[str]
    signals: list[Signal]
    top_terms: list[TermContribution]
    explanation: BilingualText
    safe_actions: BilingualList
    related_kb_slugs: list[str]
    helplines: dict[str, str]
    disclaimer: BilingualText
    model_used: bool


class ScamExample(BaseModel):
    id: int
    category: str
    language: str
    text: str
    label: str


# ---------------------------------------------------------------------- url check
class UrlCheckRequest(BaseModel):
    url: str = Field(min_length=3, max_length=2000)


class UrlBulkRequest(BaseModel):
    urls: list[str] = Field(min_length=1, max_length=20)


class UrlReason(BaseModel):
    feature: str
    value: float
    why_en: str
    why_ta: str


class UrlCheckResponse(BaseModel):
    check_id: int | None
    url_defanged: str
    risk_score: float
    risk_label: RiskLabel
    features: dict[str, float]
    top_reasons: list[UrlReason]
    lookalike_brand: str | None
    advice: BilingualText
    disclaimer: BilingualText
    model_used: bool


# ------------------------------------------------------------------------ qr / upi
class QrAnalyzeRequest(BaseModel):
    payload: str = Field(min_length=1, max_length=3000)


class QrAnalyzeResponse(BaseModel):
    payload_type: str
    risk_label: RiskLabel
    risk_score: float
    parsed: dict[str, str]
    signals: list[Signal]
    golden_rule: BilingualText
    advice: BilingualText
    disclaimer: BilingualText


class ScenarioChoice(BaseModel):
    text_en: str
    text_ta: str
    is_safe: bool
    feedback_en: str
    feedback_ta: str


class Scenario(BaseModel):
    id: str
    title_en: str
    title_ta: str
    situation_en: str
    situation_ta: str
    choices: list[ScenarioChoice]
    lesson_en: str
    lesson_ta: str


# --------------------------------------------------------------------- knowledge base
class KbArticleSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    category: str
    severity: str
    title_en: str
    title_ta: str
    summary_en: str
    summary_ta: str
    helpline: str
    views: int


class KbArticleDetail(KbArticleSummary):
    body_en: str
    body_ta: str
    red_flags: BilingualList
    safe_actions: BilingualList
    victim_steps: BilingualList
    real_example_en: str
    real_example_ta: str
    tags: str


class KbCategory(BaseModel):
    category: str
    count: int
    label_en: str
    label_ta: str


# ------------------------------------------------------------------------ assistant
class AssistantAskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    language: LanguageOrAuto = "auto"
    simple_mode: bool = False
    session_id: str | None = None


class RelatedArticle(BaseModel):
    slug: str
    title: str
    score: float


class QuickAction(BaseModel):
    """A tappable chip under the answer. `kind` maps to a frontend behaviour."""

    kind: Literal["call", "link", "route"]
    value: str
    label: str


class AssistantAskResponse(BaseModel):
    log_id: int | None
    answer: str
    language: str
    source: Literal["rule", "kb", "llm", "fallback", "refusal", "analyzer"]
    intent: str = "none"
    confidence: float
    # True when the answer needs to be acted on immediately — the UI styles it as an alert.
    urgent: bool = False
    related_articles: list[RelatedArticle]
    suggested_questions: list[str]
    quick_actions: list[QuickAction] = []
    disclaimer: str


class AssistantFeedback(BaseModel):
    log_id: int
    helpful: bool
    comment: str | None = None


# ----------------------------------------------------------------------- workshops
class WorkshopCreate(BaseModel):
    title_en: str
    title_ta: str
    venue: str
    district: str
    locality: str | None = None
    conducted_on: date
    audience_type: Literal["school", "college", "senior", "rural", "women", "mixed"] = "mixed"
    participants_expected: int = 0
    notes: str | None = None


class WorkshopOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title_en: str
    title_ta: str
    venue: str
    district: str
    locality: str | None
    conducted_on: date
    audience_type: str
    participants_expected: int
    notes: str | None


class ParticipantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    age_group: Literal["student", "adult", "senior"]
    gender: Literal["male", "female", "other"] | None = None
    language: Language = "en"
    phone: str | None = None  # hashed immediately, never stored raw
    consent_given: bool = False


class ParticipantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workshop_id: int
    name: str
    age_group: str
    gender: str | None
    language: str
    consent_given: bool


# ---------------------------------------------------------------------- assessment
class QuizOption(BaseModel):
    index: int
    text: str


class QuizQuestionOut(BaseModel):
    id: int
    category: str
    difficulty: str
    question: str
    options: list[QuizOption]


class AssessmentAnswer(BaseModel):
    question_id: int
    selected_index: int = Field(ge=0, le=3)


class AssessmentSubmit(BaseModel):
    participant_id: int
    workshop_id: int
    type: Literal["pre", "post"]
    answers: list[AssessmentAnswer]
    duration_seconds: int = 0
    language: Language = "en"


class AnswerReview(BaseModel):
    question_id: int
    question: str
    your_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str


class AssessmentResult(BaseModel):
    assessment_id: int
    score: int
    max_score: int
    percentage: float
    per_category: dict[str, dict[str, int]]
    weak_categories: list[str]
    review: list[AnswerReview]


class ImprovementResult(BaseModel):
    participant_id: int
    participant_name: str
    pre_score: int | None
    post_score: int | None
    max_score: int
    pre_percentage: float | None
    post_percentage: float | None
    # None when pre_score == 0: percentage change is undefined by division-by-zero.
    improvement_percentage: float | None
    absolute_gain: int | None
    normalized_gain: float | None
    band: str
    note: str | None = None


# ----------------------------------------------------------------------- dashboard
class DashboardTotals(BaseModel):
    workshops: int
    participants: int
    messages_analyzed: int
    urls_checked: int
    assistant_queries: int


class AwarenessStats(BaseModel):
    avg_pre_pct: float | None
    avg_post_pct: float | None
    avg_improvement_pct: float | None
    median_improvement_pct: float | None
    std_dev_improvement: float | None
    cohens_d: float | None
    t_statistic: float | None
    p_value: float | None
    n_pairs: int
    moved_to_aware_pct: float | None
    undefined_improvement_count: int
    interpretation_note: BilingualText | None = None


class CategoryDelta(BaseModel):
    category: str
    pre: float
    post: float
    delta: float


class GroupStat(BaseModel):
    group: str
    avg_pre: float
    avg_post: float
    avg_improvement: float
    n: int


class TimelinePoint(BaseModel):
    date: str
    analyses: int
    participants: int


class CountItem(BaseModel):
    name: str
    count: int


class DashboardSummary(BaseModel):
    totals: DashboardTotals
    awareness: AwarenessStats
    improvement_by_category: list[CategoryDelta]
    by_age_group: list[GroupStat]
    by_language: list[GroupStat]
    by_district: list[GroupStat]
    top_scam_categories: list[CountItem]
    risk_distribution: dict[str, int]
    timeline: list[TimelinePoint]
    feedback: dict[str, float]


class FeedbackCreate(BaseModel):
    workshop_id: int
    participant_id: int | None = None
    rating: int = Field(ge=1, le=5)
    comment: str | None = None
