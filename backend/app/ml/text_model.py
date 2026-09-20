"""Inference wrapper for the scam-text models.

Loads lazily and degrades gracefully: if the .joblib artifacts have not been trained yet, the
app still runs and the scam analyzer falls back to the rule engine alone. That matters because
a fresh clone of this repo has no artifacts until `make train` is run.
"""

from __future__ import annotations

import json
import logging
import threading

import joblib
import numpy as np

from app.config import ARTIFACT_DIR

logger = logging.getLogger(__name__)

_MODEL_PATH = ARTIFACT_DIR / "text_model.joblib"
_META_PATH = ARTIFACT_DIR / "text_model_meta.json"

_bundle: dict | None = None
_meta: dict | None = None
_lock = threading.Lock()
_load_attempted = False


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
            logger.warning("text model not found at %s — running rules-only", _MODEL_PATH)
            return None
        try:
            _bundle = joblib.load(_MODEL_PATH)
            if _META_PATH.exists():
                _meta = json.loads(_META_PATH.read_text(encoding="utf-8"))
            logger.info("text model loaded")
        except Exception:
            logger.exception("failed to load text model — running rules-only")
            _bundle = None
        return _bundle


def is_available() -> bool:
    return _load() is not None


def get_metadata() -> dict:
    _load()
    return _meta or {}


def predict_scam_probability(text: str) -> float | None:
    """P(scam) in 0..1, or None when no model is trained."""
    bundle = _load()
    if not bundle or not text.strip():
        return None
    try:
        model = bundle["binary"]
        classes = list(model.classes_)
        proba = model.predict_proba([text])[0]
        return float(proba[classes.index("scam")])
    except Exception:
        logger.exception("text model prediction failed")
        return None


def predict_category(text: str, top_k: int = 3) -> list[dict]:
    """Ranked scam categories with confidences."""
    bundle = _load()
    if not bundle or not text.strip():
        return []
    try:
        model = bundle["category"]
        classes = list(model.classes_)
        proba = model.predict_proba([text])[0]
        order = np.argsort(proba)[::-1][:top_k]
        return [
            {"name": classes[i], "confidence": round(float(proba[i]), 4)}
            for i in order
            if proba[i] > 0.01
        ]
    except Exception:
        logger.exception("category prediction failed")
        return []


def top_contributing_terms(text: str, top_k: int = 6) -> list[dict]:
    """Which tokens pushed this message toward 'scam'.

    Uses the uncalibrated LogisticRegression so coefficients are directly available, multiplied
    by the document's own TF-IDF values — a term only counts if it actually occurs here.
    """
    bundle = _load()
    if not bundle or not text.strip():
        return []
    try:
        pipe = bundle["binary_raw"]
        vec = pipe.named_steps["vec"]
        clf = pipe.named_steps["clf"]

        scam_idx = list(clf.classes_).index("scam")
        coefs = clf.coef_[0] if clf.coef_.shape[0] == 1 else clf.coef_[scam_idx]
        if clf.coef_.shape[0] == 1 and scam_idx == 0:
            coefs = -coefs  # binary LR: coef_ points at classes_[1]

        X = vec.transform([text])
        names = vec.get_feature_names_out()

        contributions = []
        # X.indices and X.data are parallel views of the same sparse row: always equal length.
        for idx, value in zip(X.indices, X.data, strict=True):
            contributions.append((names[idx], float(value * coefs[idx])))

        # Word n-grams read far better in a UI than raw character n-grams.
        words = [c for c in contributions if c[0].startswith("word__")]
        pool = words or contributions
        pool.sort(key=lambda kv: kv[1], reverse=True)

        out = []
        seen: set[str] = set()
        for name, contribution in pool:
            if contribution <= 0:
                break
            clean = name.split("__", 1)[-1].strip()
            if len(clean) < 3 or clean in seen:
                continue
            seen.add(clean)
            out.append({"term": clean, "contribution": round(contribution, 4)})
            if len(out) >= top_k:
                break
        return out
    except Exception:
        logger.exception("term attribution failed")
        return []
