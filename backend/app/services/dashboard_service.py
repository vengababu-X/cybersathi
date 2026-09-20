"""Community impact analytics."""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Assessment,
    AssistantLog,
    FeedbackEntry,
    Participant,
    QuizQuestion,
    ScamAnalysis,
    UrlCheck,
    Workshop,
)
from app.services.assessment_service import (
    AWARE_THRESHOLD,
    LOW_AWARENESS_THRESHOLD,
    compute_improvement,
    paired_t_test,
)


def _paired_records(
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
    district: str | None = None,
    audience: str | None = None,
) -> list[tuple[Participant, Assessment, Assessment]]:
    """Every participant who completed BOTH a pre-test and a post-test."""
    q = db.query(Participant, Workshop).join(Workshop, Participant.workshop_id == Workshop.id)
    if district:
        q = q.filter(Workshop.district == district)
    if audience:
        q = q.filter(Workshop.audience_type == audience)
    if date_from:
        q = q.filter(Workshop.conducted_on >= date_from)
    if date_to:
        q = q.filter(Workshop.conducted_on <= date_to)

    participants = q.all()
    if not participants:
        return []

    ids = [p.id for p, _ in participants]
    assessments = db.query(Assessment).filter(Assessment.participant_id.in_(ids)).all()

    by_participant: dict[int, dict[str, Assessment]] = defaultdict(dict)
    for a in assessments:
        by_participant[a.participant_id][a.type] = a

    paired = []
    for participant, _workshop in participants:
        entry = by_participant.get(participant.id, {})
        if "pre" in entry and "post" in entry:
            paired.append((participant, entry["pre"], entry["post"]))
    return paired


def _group_stats(rows: list[tuple[str, float, float, float | None]]) -> list[dict]:
    grouped: dict[str, list[tuple[float, float, float | None]]] = defaultdict(list)
    for key, pre, post, imp in rows:
        grouped[key].append((pre, post, imp))

    out = []
    for key, values in sorted(grouped.items()):
        pres = [v[0] for v in values]
        posts = [v[1] for v in values]
        imps = [v[2] for v in values if v[2] is not None]
        out.append(
            {
                "group": key,
                "avg_pre": round(statistics.fmean(pres), 2),
                "avg_post": round(statistics.fmean(posts), 2),
                "avg_improvement": round(statistics.fmean(imps), 2) if imps else 0.0,
                "n": len(values),
            }
        )
    return out


def summary(
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
    district: str | None = None,
    audience: str | None = None,
) -> dict:
    paired = _paired_records(db, date_from, date_to, district, audience)

    pre_pcts: list[float] = []
    post_pcts: list[float] = []
    improvements: list[float] = []
    undefined_count = 0
    moved_to_aware = 0

    age_rows: list[tuple[str, float, float, float | None]] = []
    lang_rows: list[tuple[str, float, float, float | None]] = []
    district_rows: list[tuple[str, float, float, float | None]] = []

    pre_raw: list[float] = []
    post_raw: list[float] = []

    for participant, pre, post in paired:
        result = compute_improvement(pre, post)
        if result["pre_percentage"] is None or result["post_percentage"] is None:
            continue

        pre_pct = result["pre_percentage"]
        post_pct = result["post_percentage"]
        pre_pcts.append(pre_pct)
        post_pcts.append(post_pct)
        pre_raw.append(float(pre.score))
        post_raw.append(float(post.score))

        imp = result["improvement_percentage"]
        if imp is None:
            undefined_count += 1
        else:
            improvements.append(imp)

        if pre_pct < LOW_AWARENESS_THRESHOLD and post_pct >= AWARE_THRESHOLD:
            moved_to_aware += 1

        workshop = db.query(Workshop).filter(Workshop.id == participant.workshop_id).first()
        age_rows.append((participant.age_group, pre_pct, post_pct, imp))
        lang_rows.append((participant.language, pre_pct, post_pct, imp))
        if workshop:
            district_rows.append((workshop.district, pre_pct, post_pct, imp))

    stats = paired_t_test(pre_raw, post_raw) if len(pre_raw) >= 2 else {}

    awareness = {
        "avg_pre_pct": round(statistics.fmean(pre_pcts), 2) if pre_pcts else None,
        "avg_post_pct": round(statistics.fmean(post_pcts), 2) if post_pcts else None,
        "avg_improvement_pct": round(statistics.fmean(improvements), 2) if improvements else None,
        "median_improvement_pct": round(statistics.median(improvements), 2) if improvements else None,
        "std_dev_improvement": round(statistics.stdev(improvements), 2)
        if len(improvements) > 1
        else None,
        "cohens_d": stats.get("cohens_d"),
        "t_statistic": stats.get("t_statistic"),
        "p_value": stats.get("p_value"),
        "n_pairs": len(pre_pcts),
        "moved_to_aware_pct": round(moved_to_aware / len(pre_pcts) * 100, 2) if pre_pcts else None,
        "undefined_improvement_count": undefined_count,
        "interpretation_note": None,
    }

    # Ratio-based improvement is skewed upward by small denominators: a participant going from
    # 1/10 to 5/10 registers as +400%, which drags the mean far above the typical experience.
    # Where that distortion is present, say so rather than letting the headline number stand
    # alone — the median and Cohen's d are the defensible figures to quote.
    mean_imp = awareness["avg_improvement_pct"]
    median_imp = awareness["median_improvement_pct"]
    if mean_imp is not None and median_imp is not None and mean_imp > median_imp * 1.15:
        awareness["interpretation_note"] = {
            "en": (
                f"The mean improvement ({mean_imp}%) is inflated by participants with very low "
                f"pre-test scores, where a small absolute gain becomes a very large percentage. "
                f"Quote the median ({median_imp}%) and the effect size (Cohen's d) as the "
                f"headline figures; both are robust to that distortion."
            ),
            "ta": (
                f"சராசரி முன்னேற்றம் ({mean_imp}%) மிகக் குறைந்த முன் தேர்வு மதிப்பெண் பெற்றவர்களால் "
                f"உயர்த்தப்பட்டுள்ளது — சிறிய உயர்வு கூட மிகப் பெரிய சதவீதமாகத் தெரியும். "
                f"தலைப்பு எண்ணாக இடைநிலையை ({median_imp}%) மற்றும் விளைவு அளவை (Cohen's d) "
                f"குறிப்பிடுங்கள்; இவை இரண்டும் இந்த சிதைவால் பாதிக்கப்படுவதில்லை."
            ),
        }

    # ------------------------------------------------- per-category pre vs post
    question_category = {q.id: q.category for q in db.query(QuizQuestion).all()}
    correct_map = {q.id: q.correct_index for q in db.query(QuizQuestion).all()}

    cat_totals: dict[str, dict[str, list[int]]] = defaultdict(
        lambda: {"pre_correct": [], "post_correct": []}
    )
    for _participant, pre, post in paired:
        for assessment, key in ((pre, "pre_correct"), (post, "post_correct")):
            try:
                answers = json.loads(assessment.answers_json or "[]")
            except json.JSONDecodeError:
                continue
            for ans in answers:
                qid = ans.get("question_id")
                cat = question_category.get(qid)
                if cat is None:
                    continue
                cat_totals[cat][key].append(
                    1 if ans.get("selected_index") == correct_map.get(qid) else 0
                )

    improvement_by_category = []
    for cat, data in sorted(cat_totals.items()):
        if not data["pre_correct"] or not data["post_correct"]:
            continue
        pre_v = round(statistics.fmean(data["pre_correct"]) * 100, 2)
        post_v = round(statistics.fmean(data["post_correct"]) * 100, 2)
        improvement_by_category.append(
            {"category": cat, "pre": pre_v, "post": post_v, "delta": round(post_v - pre_v, 2)}
        )

    # ------------------------------------------------------------------ totals
    totals = {
        "workshops": db.query(func.count(Workshop.id)).scalar() or 0,
        "participants": db.query(func.count(Participant.id)).scalar() or 0,
        "messages_analyzed": db.query(func.count(ScamAnalysis.id)).scalar() or 0,
        "urls_checked": db.query(func.count(UrlCheck.id)).scalar() or 0,
        "assistant_queries": db.query(func.count(AssistantLog.id)).scalar() or 0,
    }

    scam_counts = (
        db.query(ScamAnalysis.primary_category, func.count(ScamAnalysis.id))
        .group_by(ScamAnalysis.primary_category)
        .order_by(func.count(ScamAnalysis.id).desc())
        .limit(8)
        .all()
    )
    top_scam_categories = [{"name": c or "unknown", "count": n} for c, n in scam_counts]

    risk_counts = (
        db.query(ScamAnalysis.risk_label, func.count(ScamAnalysis.id))
        .group_by(ScamAnalysis.risk_label)
        .all()
    )
    risk_distribution = {"safe": 0, "suspicious": 0, "high_risk": 0}
    for label, n in risk_counts:
        if label in risk_distribution:
            risk_distribution[label] = n

    # ---------------------------------------------------------------- timeline
    since = datetime.now(UTC) - timedelta(days=90)
    analyses_by_day = (
        db.query(func.date(ScamAnalysis.created_at), func.count(ScamAnalysis.id))
        .filter(ScamAnalysis.created_at >= since)
        .group_by(func.date(ScamAnalysis.created_at))
        .all()
    )
    participants_by_day = (
        db.query(func.date(Participant.created_at), func.count(Participant.id))
        .filter(Participant.created_at >= since)
        .group_by(func.date(Participant.created_at))
        .all()
    )
    day_map: dict[str, dict[str, int]] = defaultdict(lambda: {"analyses": 0, "participants": 0})
    for day, n in analyses_by_day:
        day_map[str(day)]["analyses"] = n
    for day, n in participants_by_day:
        day_map[str(day)]["participants"] = n
    timeline = [
        {"date": d, "analyses": v["analyses"], "participants": v["participants"]}
        for d, v in sorted(day_map.items())
    ]

    feedback_rows = db.query(FeedbackEntry.rating).all()
    ratings = [r[0] for r in feedback_rows]
    feedback = {
        "avg_rating": round(statistics.fmean(ratings), 2) if ratings else 0.0,
        "count": float(len(ratings)),
    }

    return {
        "totals": totals,
        "awareness": awareness,
        "improvement_by_category": improvement_by_category,
        "by_age_group": _group_stats(age_rows),
        "by_language": _group_stats(lang_rows),
        "by_district": _group_stats(district_rows),
        "top_scam_categories": top_scam_categories,
        "risk_distribution": risk_distribution,
        "timeline": timeline,
        "feedback": feedback,
    }


def export_rows(db: Session) -> list[dict]:
    """Flat per-participant rows for the CSV impact report."""
    paired_all = _paired_records(db)
    rows = []
    for participant, pre, post in paired_all:
        workshop = db.query(Workshop).filter(Workshop.id == participant.workshop_id).first()
        result = compute_improvement(pre, post)
        rows.append(
            {
                "participant_id": participant.id,
                "name": participant.name,
                "age_group": participant.age_group,
                "gender": participant.gender or "",
                "language": participant.language,
                "workshop": workshop.title_en if workshop else "",
                "district": workshop.district if workshop else "",
                "audience_type": workshop.audience_type if workshop else "",
                "conducted_on": str(workshop.conducted_on) if workshop else "",
                "pre_score": result["pre_score"],
                "post_score": result["post_score"],
                "max_score": result["max_score"],
                "pre_percentage": result["pre_percentage"],
                "post_percentage": result["post_percentage"],
                "improvement_percentage": result["improvement_percentage"],
                "absolute_gain": result["absolute_gain"],
                "normalized_gain": result["normalized_gain"],
                "band": result["band"],
                "note": result["note"] or "",
            }
        )
    return rows
