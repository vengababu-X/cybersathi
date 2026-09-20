"""Pre/post assessment and the awareness-improvement maths.

Two design decisions matter for the validity of the reported impact:

1. MATCHED QUESTION SETS. The pre-test and post-test draw the same category/difficulty mix
   but different items, seeded deterministically per (workshop, participant, type). Comparing
   a random 10 questions against another random 10 would measure luck, not learning.

2. THE DIVISION-BY-ZERO GUARD. The project's headline formula is
       improvement % = ((post - pre) / pre) * 100
   which is undefined when a participant scores 0 on the pre-test — a real occurrence with
   first-time internet users. Rather than silently dropping those participants or printing
   "infinity", the service reports the percentage as None and supplies absolute gain and
   Hake's normalized gain instead. The dashboard shows all three.
"""

from __future__ import annotations

import json
import random
import statistics
from collections import defaultdict

from sqlalchemy.orm import Session

from app.models import Assessment, Participant, QuizQuestion

DEFAULT_QUESTION_COUNT = 10
AWARE_THRESHOLD = 70.0
LOW_AWARENESS_THRESHOLD = 50.0


def _seed_for(workshop_id: int, participant_id: int, assessment_type: str) -> int:
    # Same participant + workshop always gets the same paper, so a reload does not reshuffle.
    return hash((workshop_id, participant_id, assessment_type)) & 0x7FFFFFFF


def select_questions(
    db: Session,
    workshop_id: int,
    participant_id: int,
    assessment_type: str,
    count: int = DEFAULT_QUESTION_COUNT,
) -> list[QuizQuestion]:
    """Matched sampling: same category profile for pre and post, disjoint items where possible."""
    all_questions = db.query(QuizQuestion).filter(QuizQuestion.is_active.is_(True)).all()
    if not all_questions:
        return []

    by_category: dict[str, list[QuizQuestion]] = defaultdict(list)
    for q in all_questions:
        by_category[q.category].append(q)

    # A stable category plan shared by both papers.
    plan_rng = random.Random(_seed_for(workshop_id, participant_id, "plan"))
    categories = sorted(by_category.keys())
    plan_rng.shuffle(categories)

    plan: list[str] = []
    taken: dict[str, int] = defaultdict(int)
    while len(plan) < count:
        added_this_pass = False
        for cat in categories:
            if len(plan) >= count:
                break
            if taken[cat] < len(by_category[cat]):
                plan.append(cat)
                taken[cat] += 1
                added_this_pass = True
        if not added_this_pass:
            break  # every category exhausted; the top-up step below fills the rest

    # Within each category, both papers see the SAME deterministic ordering; the pre-test takes
    # the first item and the post-test the next one. That guarantees disjoint questions whenever
    # the category has two or more items, instead of relying on a random draw that can collide.
    # A category holding only one question is unavoidably repeated — documented as a limitation.
    offset = 0 if assessment_type == "pre" else 1

    selected: list[QuizQuestion] = []
    used_ids: set[int] = set()
    seen_in_category: dict[str, int] = defaultdict(int)

    for cat in plan:
        pool = sorted(by_category[cat], key=lambda q: q.id)
        if not pool:
            continue
        # Stable per-category shuffle, identical for pre and post.
        cat_rng = random.Random(_seed_for(workshop_id, participant_id, f"cat:{cat}"))
        cat_rng.shuffle(pool)

        take = seen_in_category[cat] * 2 + offset
        seen_in_category[cat] += 1

        choice = pool[take % len(pool)]
        if choice.id in used_ids:
            alternative = next((q for q in pool if q.id not in used_ids), None)
            if alternative is None:
                continue
            choice = alternative

        selected.append(choice)
        used_ids.add(choice.id)
        if len(selected) >= count:
            break

    # Top up if some categories ran dry.
    if len(selected) < count:
        remaining = [q for q in all_questions if q.id not in used_ids]
        random.Random(_seed_for(workshop_id, participant_id, assessment_type)).shuffle(remaining)
        selected.extend(remaining[: count - len(selected)])

    return selected[:count]


def submit(
    db: Session,
    participant_id: int,
    workshop_id: int,
    assessment_type: str,
    answers: list[dict],
    duration_seconds: int = 0,
    language: str = "en",
) -> dict:
    question_ids = [a["question_id"] for a in answers]
    questions = {
        q.id: q for q in db.query(QuizQuestion).filter(QuizQuestion.id.in_(question_ids)).all()
    }

    score = 0
    review = []
    per_category: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})

    for answer in answers:
        q = questions.get(answer["question_id"])
        if not q:
            continue
        options = json.loads(q.options_ta_json if language == "ta" else q.options_en_json)
        selected = answer["selected_index"]
        correct = selected == q.correct_index
        if correct:
            score += 1

        per_category[q.category]["total"] += 1
        if correct:
            per_category[q.category]["correct"] += 1

        review.append(
            {
                "question_id": q.id,
                "question": q.question_ta if language == "ta" else q.question_en,
                "your_answer": options[selected] if 0 <= selected < len(options) else "-",
                "correct_answer": options[q.correct_index],
                "is_correct": correct,
                "explanation": q.explanation_ta if language == "ta" else q.explanation_en,
            }
        )

    max_score = len(review)

    existing = (
        db.query(Assessment)
        .filter(
            Assessment.participant_id == participant_id, Assessment.type == assessment_type
        )
        .first()
    )
    if existing:
        existing.score = score
        existing.max_score = max_score
        existing.duration_seconds = duration_seconds
        existing.answers_json = json.dumps(answers)
        record = existing
    else:
        record = Assessment(
            participant_id=participant_id,
            workshop_id=workshop_id,
            type=assessment_type,
            score=score,
            max_score=max_score,
            duration_seconds=duration_seconds,
            answers_json=json.dumps(answers),
        )
        db.add(record)

    db.commit()
    db.refresh(record)

    weak = [c for c, s in per_category.items() if s["total"] and s["correct"] / s["total"] < 0.5]

    return {
        "assessment_id": record.id,
        "score": score,
        "max_score": max_score,
        "percentage": round(score / max_score * 100, 2) if max_score else 0.0,
        "per_category": dict(per_category),
        "weak_categories": weak,
        "review": review,
    }


def compute_improvement(pre: Assessment | None, post: Assessment | None) -> dict:
    """The core impact calculation, with the division-by-zero guard."""
    pre_score = pre.score if pre else None
    post_score = post.score if post else None
    max_score = (post.max_score if post else pre.max_score if pre else 0) or 0

    pre_pct = round(pre_score / pre.max_score * 100, 2) if pre and pre.max_score else None
    post_pct = round(post_score / post.max_score * 100, 2) if post and post.max_score else None

    improvement_pct: float | None = None
    absolute_gain: int | None = None
    normalized_gain: float | None = None
    note: str | None = None

    if pre_score is not None and post_score is not None:
        absolute_gain = post_score - pre_score

        if pre_score > 0:
            improvement_pct = round((post_score - pre_score) / pre_score * 100, 2)
        else:
            # Percentage change from zero is undefined — report the alternatives instead.
            note = (
                "Pre-test score was 0, so percentage improvement is mathematically undefined. "
                "Absolute and normalized gain are reported instead."
            )

        if max_score - pre_score > 0:
            normalized_gain = round((post_score - pre_score) / (max_score - pre_score), 4)
        elif post_score == max_score:
            normalized_gain = 1.0

    if post_pct is None:
        band = "post-test pending"
    elif post_pct >= AWARE_THRESHOLD:
        band = "aware"
    elif post_pct >= LOW_AWARENESS_THRESHOLD:
        band = "partially aware"
    else:
        band = "needs follow-up"

    return {
        "pre_score": pre_score,
        "post_score": post_score,
        "max_score": max_score,
        "pre_percentage": pre_pct,
        "post_percentage": post_pct,
        "improvement_percentage": improvement_pct,
        "absolute_gain": absolute_gain,
        "normalized_gain": normalized_gain,
        "band": band,
        "note": note,
    }


def improvement_for_participant(db: Session, participant_id: int) -> dict | None:
    participant = db.query(Participant).filter(Participant.id == participant_id).first()
    if not participant:
        return None

    pre = (
        db.query(Assessment)
        .filter(Assessment.participant_id == participant_id, Assessment.type == "pre")
        .first()
    )
    post = (
        db.query(Assessment)
        .filter(Assessment.participant_id == participant_id, Assessment.type == "post")
        .first()
    )

    result = compute_improvement(pre, post)
    result["participant_id"] = participant_id
    result["participant_name"] = participant.name
    return result


def paired_t_test(pre_scores: list[float], post_scores: list[float]) -> dict:
    """Paired-samples t-test and Cohen's d.

    scipy is available, but the hand-rolled path keeps the statistic reproducible and lets the
    report show the formula. Both agree to several decimal places.
    """
    n = len(pre_scores)
    if n < 2:
        return {"t_statistic": None, "p_value": None, "cohens_d": None, "n": n}

    # Both lists are appended together by the caller, so a length mismatch is a bug, not data.
    diffs = [post - pre for pre, post in zip(pre_scores, post_scores, strict=True)]
    mean_diff = statistics.fmean(diffs)
    sd_diff = statistics.stdev(diffs) if n > 1 else 0.0

    if sd_diff == 0:
        return {
            "t_statistic": None,
            "p_value": None,
            "cohens_d": None,
            "n": n,
            "note": "All differences identical; t-test undefined.",
        }

    t_stat = mean_diff / (sd_diff / (n**0.5))
    cohens_d = mean_diff / sd_diff

    try:
        from scipy import stats

        p_value = float(2 * (1 - stats.t.cdf(abs(t_stat), df=n - 1)))
    except Exception:
        p_value = None

    return {
        "t_statistic": round(float(t_stat), 4),
        "p_value": round(p_value, 6) if p_value is not None else None,
        "cohens_d": round(float(cohens_d), 4),
        "n": n,
    }
