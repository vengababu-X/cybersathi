"""TF-IDF retrieval over the knowledge base.

This is what makes the assistant work with no LLM and no API key: the answer is composed from
a real article rather than generated, so it cannot invent a helpline number or fabricate advice.

Important: the cached index holds plain dicts, never SQLAlchemy ORM instances. ORM objects are
bound to the session that loaded them, and that session closes when the request ends — caching
them across requests raises DetachedInstanceError the moment an attribute is touched.
"""

from __future__ import annotations

import json
import logging
import threading

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models import KbArticle

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_index: dict[str, dict] = {}  # language -> {vectoriser, matrix, articles}

# Below this cosine similarity the match is treated as "no good answer" and the assistant
# falls back rather than confidently returning an unrelated article.
MIN_SIMILARITY = 0.10


def to_dict(article: KbArticle) -> dict:
    """Detach the article into a plain dict while the session is still open."""
    return {
        "id": article.id,
        "slug": article.slug,
        "category": article.category,
        "severity": article.severity,
        "title_en": article.title_en,
        "title_ta": article.title_ta,
        "summary_en": article.summary_en,
        "summary_ta": article.summary_ta,
        "body_en": article.body_en,
        "body_ta": article.body_ta,
        "red_flags_json": article.red_flags_json,
        "safe_actions_json": article.safe_actions_json,
        "victim_steps_json": article.victim_steps_json,
        "helpline": article.helpline,
        "tags": article.tags or "",
    }


def _document_for(article: dict, language: str) -> str:
    """Build the indexed text.

    Title, summary, tags and category are repeated so they outweigh the body. Without this the
    ~250-word body dominates the vector and a short, direct question like "someone is asking
    for my OTP" scores below threshold against its own article.
    """
    if language == "ta":
        title, summary, body = article["title_ta"], article["summary_ta"], article["body_ta"]
    else:
        title, summary, body = article["title_en"], article["summary_en"], article["body_en"]

    tags = article["tags"].replace(",", " ")
    category = article["category"].replace("_", " ")

    parts = [
        title, title, title,
        summary, summary,
        tags, tags, tags,
        category, category,
        body,
    ]
    return " ".join(p for p in parts if p)


def build_index(db: Session, language: str) -> dict | None:
    rows = db.query(KbArticle).all()
    if not rows:
        return None

    articles = [to_dict(a) for a in rows]
    docs = [_document_for(a, language) for a in articles]

    if language == "ta":
        # char_wb for Tamil: word tokenisation alone is weak on an agglutinative script,
        # where the same root carries many suffixes.
        vectoriser = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(2, 4), sublinear_tf=True, lowercase=True, min_df=1
        )
    else:
        vectoriser = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            sublinear_tf=True,
            lowercase=True,
            min_df=1,
            stop_words="english",
        )

    matrix = vectoriser.fit_transform(docs)
    return {"vectoriser": vectoriser, "matrix": matrix, "articles": articles}


def get_index(db: Session, language: str) -> dict | None:
    with _lock:
        if language not in _index:
            built = build_index(db, language)
            if built is None:
                return None
            _index[language] = built
        return _index[language]


def invalidate() -> None:
    """Call after any knowledge-base write so the next query rebuilds."""
    with _lock:
        _index.clear()


def search(db: Session, query: str, language: str = "en", top_k: int = 3) -> list[dict]:
    """Return [{article: dict, score: float}] ordered by relevance."""
    if not query or not query.strip():
        return []

    index = get_index(db, language)
    if index is None:
        return []

    try:
        qv = index["vectoriser"].transform([query])
        sims = cosine_similarity(qv, index["matrix"])[0]
    except Exception:
        logger.exception("retrieval failed")
        return []

    # One similarity per indexed article, by construction in build_index().
    ranked = sorted(zip(index["articles"], sims, strict=True), key=lambda t: t[1], reverse=True)
    return [
        {"article": article, "score": round(float(score), 4)}
        for article, score in ranked[:top_k]
        if score > 0
    ]


def best_match(db: Session, query: str, language: str = "en") -> tuple[dict | None, float]:
    results = search(db, query, language, top_k=1)
    if not results:
        return None, 0.0
    return results[0]["article"], results[0]["score"]


def compose_answer(article: dict, language: str, simple_mode: bool = False) -> str:
    """Build the assistant reply from the article's own fields."""
    is_ta = language == "ta"
    summary = article["summary_ta"] if is_ta else article["summary_en"]

    try:
        flags = json.loads(article["red_flags_json"] or "{}")
        actions = json.loads(article["safe_actions_json"] or "{}")
    except (json.JSONDecodeError, TypeError):
        flags, actions = {}, {}

    flag_list = (flags.get("ta") if is_ta else flags.get("en")) or []
    action_list = (actions.get("ta") if is_ta else actions.get("en")) or []

    if simple_mode:
        # Short sentences only, one flag and one action — for first-time or elderly users.
        lead = summary.split(".")[0].strip()
        parts = [lead + "."]
        if flag_list:
            parts.append(("கவனிக்க: " if is_ta else "Watch for: ") + flag_list[0])
        if action_list:
            parts.append(("செய்ய வேண்டியது: " if is_ta else "Do this: ") + action_list[0])
        parts.append("உதவி: 1930-ஐ அழையுங்கள்." if is_ta else "Help: call 1930.")
        return "\n".join(parts)

    header_flags = "எச்சரிக்கை அறிகுறிகள்:" if is_ta else "Warning signs:"
    header_actions = "பாதுகாப்பான நடவடிக்கை:" if is_ta else "What to do:"
    footer = (
        "சந்தேகம் இருந்தால் 1930-ஐ அழையுங்கள் அல்லது cybercrime.gov.in-ல் புகார் அளியுங்கள்."
        if is_ta
        else "If in doubt, call 1930 or report at cybercrime.gov.in."
    )

    lines = [summary, "", header_flags]
    lines += [f"• {f}" for f in flag_list[:3]]
    lines += ["", header_actions]
    lines += [f"• {a}" for a in action_list[:3]]
    lines += ["", footer]
    return "\n".join(lines)
