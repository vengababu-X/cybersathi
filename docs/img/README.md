# Generated figures

These files are written by `backend/ml_training/evaluate.py` and referenced from
[`../ML_METRICS.md`](../ML_METRICS.md). Do not edit them by hand — re-run the script instead:

```bash
cd backend
.venv/Scripts/python.exe ml_training/evaluate.py
```

| File | What it shows |
|---|---|
| `confusion_text.png` | Confusion matrix for the scam-message classifier on the held-out test split |
| `confusion_url.png` | Confusion matrix for the phishing-URL classifier on the held-out test split |
| `feature_importance_url.png` | The twelve most influential static URL features |

They are drawn with Pillow rather than matplotlib: Pillow already arrives as a `reportlab`
dependency, so the project gains figures without adding a second plotting stack to
`requirements.txt`. Both diagrams in `docs/ARCHITECTURE.md` are Mermaid sources instead, which
GitHub renders directly, so they are not duplicated here as images.
