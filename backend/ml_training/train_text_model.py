"""Train the scam-message classifiers.

Two models are produced from the same corpus:
  1. binary   — scam vs legitimate  (drives the risk score)
  2. category — which scam family it is (drives the explanation and the KB link)

Word TF-IDF alone handles English poorly on Tanglish and misses Tamil morphology, so the
vectoriser is a union of word n-grams and character n-grams. Character n-grams are what make
"pannunga"/"panunga" and Tamil suffix variation work without a stemmer.

Run:  python ml_training/train_text_model.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import joblib
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split
from sklearn.pipeline import FeatureUnion, Pipeline

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data"
ARTIFACTS = BASE / "app" / "ml" / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42


def build_vectoriser() -> FeatureUnion:
    return FeatureUnion(
        [
            (
                "word",
                TfidfVectorizer(
                    analyzer="word",
                    ngram_range=(1, 2),
                    sublinear_tf=True,
                    min_df=2,
                    max_features=20000,
                    lowercase=True,
                ),
            ),
            (
                "char",
                TfidfVectorizer(
                    analyzer="char_wb",
                    ngram_range=(3, 5),
                    sublinear_tf=True,
                    min_df=2,
                    max_features=30000,
                    lowercase=True,
                ),
            ),
        ]
    )


def main() -> int:
    csv_path = DATA / "scam_messages.csv"
    if not csv_path.exists():
        print("ERROR: dataset missing. Run ml_training/generate_datasets.py first.")
        return 1

    df = pd.read_csv(csv_path)
    df = df.dropna(subset=["text", "label"])
    print(f"corpus: {len(df)} rows | scam={sum(df.label=='scam')} legitimate={sum(df.label=='legitimate')}")
    print(f"languages: {df.language.value_counts().to_dict()}")

    # ---------------------------------------------------------------- binary model
    X, y = df["text"].astype(str), df["label"].astype(str)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    pipe = Pipeline(
        [
            ("vec", build_vectoriser()),
            (
                "clf",
                LogisticRegression(
                    max_iter=3000, class_weight="balanced", random_state=RANDOM_STATE
                ),
            ),
        ]
    )

    grid = GridSearchCV(
        pipe,
        {"clf__C": [1.0, 4.0, 10.0]},
        cv=5,
        scoring="f1_macro",
        n_jobs=1,
        verbose=0,
    )
    grid.fit(X_tr, y_tr)
    best = grid.best_estimator_
    print(f"\n[binary] best params: {grid.best_params_}  cv f1_macro={grid.best_score_:.4f}")

    y_pred = best.predict(X_te)
    report = classification_report(y_te, y_pred, output_dict=True, zero_division=0)
    print(classification_report(y_te, y_pred, zero_division=0))
    print("confusion matrix (rows=true [legitimate, scam]):")
    cm = confusion_matrix(y_te, y_pred, labels=["legitimate", "scam"])
    print(cm)

    cv_scores = cross_val_score(best, X, y, cv=5, scoring="f1_macro", n_jobs=1)
    print(f"[binary] 5-fold f1_macro on full data: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    # Calibrated probabilities: the risk score is shown to users as a number out of 100, so an
    # uncalibrated margin would be misleading.
    calibrated = CalibratedClassifierCV(best, method="sigmoid", cv=5)
    calibrated.fit(X_tr, y_tr)

    # ---------------------------------------------------------------- category model
    cat_df = df[df["label"] == "scam"]
    Xc, yc = cat_df["text"].astype(str), cat_df["category"].astype(str)
    keep = yc.value_counts()[lambda s: s >= 8].index
    mask = yc.isin(keep)
    Xc, yc = Xc[mask], yc[mask]

    Xc_tr, Xc_te, yc_tr, yc_te = train_test_split(
        Xc, yc, test_size=0.2, stratify=yc, random_state=RANDOM_STATE
    )
    cat_pipe = Pipeline(
        [
            ("vec", build_vectoriser()),
            ("clf", LogisticRegression(max_iter=3000, class_weight="balanced",
                                       C=6.0, random_state=RANDOM_STATE)),
        ]
    )
    cat_pipe.fit(Xc_tr, yc_tr)
    cat_pred = cat_pipe.predict(Xc_te)
    cat_report = classification_report(yc_te, cat_pred, output_dict=True, zero_division=0)
    print(f"\n[category] classes: {sorted(set(yc))}")
    print(f"[category] accuracy: {cat_report['accuracy']:.4f}  macro-F1: {cat_report['macro avg']['f1-score']:.4f}")

    # ---------------------------------------------------------------- persist
    joblib.dump(
        {
            "binary": calibrated,
            "binary_raw": best,
            "category": cat_pipe,
            "classes_binary": list(calibrated.classes_),
            "classes_category": list(cat_pipe.classes_),
        },
        ARTIFACTS / "text_model.joblib",
        compress=3,
    )

    meta = {
        "trained_at": datetime.now(UTC).isoformat(),
        "rows": len(df),
        "rows_scam": int(sum(df.label == "scam")),
        "rows_legitimate": int(sum(df.label == "legitimate")),
        "rows_tamil": int(sum(df.language == "ta")),
        "binary_best_params": {k: str(v) for k, v in grid.best_params_.items()},
        "binary_cv_f1_macro": round(float(cv_scores.mean()), 4),
        "binary_cv_std": round(float(cv_scores.std()), 4),
        "binary_test_accuracy": round(float(report["accuracy"]), 4),
        "binary_test_macro_f1": round(float(report["macro avg"]["f1-score"]), 4),
        "binary_precision_scam": round(float(report["scam"]["precision"]), 4),
        "binary_recall_scam": round(float(report["scam"]["recall"]), 4),
        "confusion_matrix": cm.tolist(),
        "confusion_labels": ["legitimate", "scam"],
        "category_classes": sorted(set(yc)),
        "category_accuracy": round(float(cat_report["accuracy"]), 4),
        "category_macro_f1": round(float(cat_report["macro avg"]["f1-score"]), 4),
    }
    (ARTIFACTS / "text_model_meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    target = 0.90
    got = meta["binary_test_macro_f1"]
    print(f"\nsaved -> {ARTIFACTS / 'text_model.joblib'}")
    print(f"macro-F1 {got:.4f} vs target {target:.2f}: {'PASS' if got >= target else 'BELOW TARGET'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
