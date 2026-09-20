"""Train the phishing-URL classifier on static, network-free features.

RandomForest rather than LogisticRegression here: the URL signals interact non-linearly
(an IP host is damning on its own; a hyphen only matters together with a brand keyword),
and the tree ensemble gives per-feature importances that map cleanly onto the "why" shown
to the user.

Run:  python ml_training/train_url_model.py
"""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import GridSearchCV, cross_val_score, train_test_split

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from app.ml.features import FEATURE_NAMES, extract_url_features  # noqa: E402

DATA = BASE / "data"
ARTIFACTS = BASE / "app" / "ml" / "artifacts"
ARTIFACTS.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42


def main() -> int:
    csv_path = DATA / "urls.csv"
    if not csv_path.exists():
        print("ERROR: dataset missing. Run ml_training/generate_datasets.py first.")
        return 1

    df = pd.read_csv(csv_path).dropna(subset=["url", "label"])
    print(f"corpus: {len(df)} urls | phishing={sum(df.label=='phishing')} safe={sum(df.label=='safe')}")

    feats = [extract_url_features(u) for u in df["url"].astype(str)]
    X = np.array([[f[name] for name in FEATURE_NAMES] for f in feats], dtype=float)
    y = df["label"].astype(str).to_numpy()

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE
    )

    grid = GridSearchCV(
        RandomForestClassifier(class_weight="balanced", random_state=RANDOM_STATE, n_jobs=1),
        {
            "n_estimators": [200, 400],
            "max_depth": [None, 12],
            "min_samples_leaf": [1, 2],
        },
        cv=5,
        scoring="f1_macro",
        n_jobs=1,
    )
    grid.fit(X_tr, y_tr)
    model = grid.best_estimator_
    print(f"\nbest params: {grid.best_params_}  cv f1_macro={grid.best_score_:.4f}")

    y_pred = model.predict(X_te)
    report = classification_report(y_te, y_pred, output_dict=True, zero_division=0)
    print(classification_report(y_te, y_pred, zero_division=0))

    cm = confusion_matrix(y_te, y_pred, labels=["safe", "phishing"])
    print("confusion matrix (rows=true [safe, phishing]):")
    print(cm)

    phish_idx = list(model.classes_).index("phishing")
    proba = model.predict_proba(X_te)[:, phish_idx]
    auc = roc_auc_score((y_te == "phishing").astype(int), proba)
    print(f"ROC-AUC: {auc:.4f}")

    cv_scores = cross_val_score(model, X, y, cv=5, scoring="f1_macro", n_jobs=1)
    print(f"5-fold f1_macro on full data: {cv_scores.mean():.4f} (+/- {cv_scores.std():.4f})")

    importances = sorted(
        zip(FEATURE_NAMES, model.feature_importances_, strict=True),
        key=lambda kv: kv[1],
        reverse=True,
    )
    print("\ntop 10 features:")
    for name, imp in importances[:10]:
        print(f"  {name:24s} {imp:.4f}")

    joblib.dump(
        {"model": model, "feature_names": FEATURE_NAMES, "classes": list(model.classes_)},
        ARTIFACTS / "url_model.joblib",
        compress=3,
    )

    meta = {
        "trained_at": datetime.now(UTC).isoformat(),
        "rows": len(df),
        "rows_phishing": int(sum(df.label == "phishing")),
        "rows_safe": int(sum(df.label == "safe")),
        "best_params": {k: str(v) for k, v in grid.best_params_.items()},
        "test_accuracy": round(float(report["accuracy"]), 4),
        "test_macro_f1": round(float(report["macro avg"]["f1-score"]), 4),
        "precision_phishing": round(float(report["phishing"]["precision"]), 4),
        "recall_phishing": round(float(report["phishing"]["recall"]), 4),
        "roc_auc": round(float(auc), 4),
        "cv_f1_macro": round(float(cv_scores.mean()), 4),
        "cv_std": round(float(cv_scores.std()), 4),
        "confusion_matrix": cm.tolist(),
        "confusion_labels": ["safe", "phishing"],
        "feature_importances": [{"feature": n, "importance": round(float(i), 5)} for n, i in importances],
    }
    (ARTIFACTS / "url_model_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )

    target = 0.92
    got = meta["test_accuracy"]
    print(f"\nsaved -> {ARTIFACTS / 'url_model.joblib'}")
    print(f"accuracy {got:.4f} vs target {target:.2f}: {'PASS' if got >= target else 'BELOW TARGET'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
