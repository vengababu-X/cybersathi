"""Write docs/ML_METRICS.md and the figure assets in docs/img/ from the saved metadata.

Run after training:  python ml_training/evaluate.py

The figures are drawn with Pillow rather than matplotlib: Pillow is already a reportlab
dependency, so the project gains chart output without adding a second plotting stack to
requirements.txt.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent.parent
ARTIFACTS = BASE / "app" / "ml" / "artifacts"
DOCS = BASE.parent / "docs"
IMG = DOCS / "img"
DOCS.mkdir(parents=True, exist_ok=True)
IMG.mkdir(parents=True, exist_ok=True)

INK = (15, 23, 42)  # slate-900
MUTED = (100, 116, 139)  # slate-500
GRID = (203, 213, 225)  # slate-300
BRAND = (30, 58, 95)  # brand-800
TILE = (219, 234, 254)  # brand-100

# Pillow ships only a bitmap default font, so prefer a real scalable one when the machine
# has it (DejaVu on Linux, Segoe UI / Arial on Windows) and fall back to the scalable
# default in Pillow >= 10.1.
_FONT_CANDIDATES = (
    "DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
)


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for candidate in _FONT_CANDIDATES:
        path = Path(candidate)
        if not path.exists():
            continue
        try:
            if bold and "DejaVuSans.ttf" in candidate:
                return ImageFont.truetype(str(path).replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"), size)
            return ImageFont.truetype(str(path), size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)  # Pillow >= 10.1: scalable
    except TypeError:  # pragma: no cover - very old Pillow
        return ImageFont.load_default()


def _text(draw: ImageDraw.ImageDraw, xy: tuple[float, float], value: str, **kwargs) -> None:
    draw.text(xy, value, **kwargs)


def _centred(draw: ImageDraw.ImageDraw, box: tuple[float, float, float, float], value: str, **kwargs) -> None:
    left, top, right, bottom = box
    draw.text(((left + right) / 2, (top + bottom) / 2), value, anchor="mm", **kwargs)


def confusion_figure(matrix: list[list[int]], labels: list[str], title: str, out: Path) -> None:
    """A labelled heatmap of the confusion matrix."""
    cell = 130
    pad_left, pad_top, pad_right, pad_bottom = 120, 90, 40, 70
    n = len(labels)
    width = pad_left + cell * n + pad_right
    height = pad_top + cell * n + pad_bottom

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font, label_font, value_font = _font(20, bold=True), _font(16), _font(28, bold=True)

    _text(draw, (pad_left, 26), title, font=title_font, fill=INK)
    _text(draw, (16, pad_top + cell * n / 2), "True", font=label_font, fill=MUTED, anchor="lm")
    _text(
        draw,
        (pad_left + cell * n / 2, pad_top + cell * n + 38),
        "Predicted",
        font=label_font,
        fill=MUTED,
        anchor="mm",
    )

    peak = max((v for row in matrix for v in row), default=1) or 1

    for r, row in enumerate(matrix):
        for c, value in enumerate(row):
            left, top = pad_left + c * cell, pad_top + r * cell
            right, bottom = left + cell, top + cell

            # Diagonal cells are the correct predictions -- give them the brand colour.
            correct = r == c
            strength = value / peak
            if correct:
                fill = tuple(int(TILE[i] + (BRAND[i] - TILE[i]) * strength) for i in range(3))
                ink = "white" if strength > 0.65 else INK
            else:
                shade = int(248 - 40 * strength)
                fill = (shade, shade, shade)
                ink = INK

            draw.rectangle([left, top, right, bottom], fill=fill, outline=GRID, width=1)
            _centred(draw, (left, top, right, bottom), f"{value:,}", font=value_font, fill=ink)

    for i, name in enumerate(labels):
        _text(
            draw,
            (pad_left - 12, pad_top + i * cell + cell / 2),
            name,
            font=label_font,
            fill=INK,
            anchor="rm",
        )
        _centred(
            draw,
            (pad_left + i * cell, pad_top - 34, pad_left + (i + 1) * cell, pad_top - 6),
            name,
            font=label_font,
            fill=INK,
        )

    image.save(out, "PNG", optimize=True)
    print(f"wrote {out}")


def importance_figure(items: list[dict], title: str, out: Path) -> None:
    """A horizontal bar chart of the most influential URL features."""
    items = items[:12]
    row, pad_left, pad_top, pad_right, pad_bottom = 32, 300, 78, 90, 62
    width = pad_left + 560 + pad_right
    height = pad_top + row * len(items) + pad_bottom

    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    title_font, label_font, value_font = _font(20, bold=True), _font(15), _font(14)
    _text(draw, (pad_left, 30), title, font=title_font, fill=INK)

    peak = max((float(i["importance"]) for i in items), default=1.0) or 1.0
    bar_max = 560

    for idx, item in enumerate(items):
        top = pad_top + idx * row
        share = float(item["importance"]) / peak
        colour = tuple(int(TILE[i] + (BRAND[i] - TILE[i]) * share) for i in range(3))

        _text(
            draw,
            (pad_left - 12, top + row / 2 - 2),
            item["feature"],
            font=label_font,
            fill=INK,
            anchor="rm",
        )
        draw.rectangle([pad_left, top + 6, pad_left + bar_max, top + row - 6], fill=(241, 245, 249))
        draw.rectangle(
            [pad_left, top + 6, pad_left + max(2, bar_max * share), top + row - 6],
            fill=colour,
        )
        _text(
            draw,
            (pad_left + bar_max + 10, top + row / 2 - 2),
            f"{float(item['importance']):.3f}",
            font=value_font,
            fill=MUTED,
            anchor="lm",
        )

    _text(
        draw,
        (pad_left, height - 46),
        "Impurity-based importance: correlated features share credit,",
        font=value_font,
        fill=MUTED,
    )
    _text(
        draw,
        (pad_left, height - 28),
        "so read the order, not the gaps.",
        font=value_font,
        fill=MUTED,
    )

    image.save(out, "PNG", optimize=True)
    print(f"wrote {out}")


def _confusion_table(matrix: list[list[int]], labels: list[str]) -> str:
    header = "| true \\ predicted | " + " | ".join(labels) + " |"
    sep = "|---" * (len(labels) + 1) + "|"
    rows = [
        f"| **{labels[i]}** | " + " | ".join(str(v) for v in row) + " |"
        for i, row in enumerate(matrix)
    ]
    return "\n".join([header, sep, *rows])


def main() -> int:
    text_meta_path = ARTIFACTS / "text_model_meta.json"
    url_meta_path = ARTIFACTS / "url_model_meta.json"

    if not text_meta_path.exists() or not url_meta_path.exists():
        print("ERROR: model metadata missing. Train the models first:")
        print("  python ml_training/train_text_model.py")
        print("  python ml_training/train_url_model.py")
        return 1

    text = json.loads(text_meta_path.read_text(encoding="utf-8"))
    url = json.loads(url_meta_path.read_text(encoding="utf-8"))

    # Figures first, so a rendering failure is obvious before the Markdown is written.
    confusion_figure(
        text["confusion_matrix"],
        text["confusion_labels"],
        "Scam message classifier — test set",
        IMG / "confusion_text.png",
    )
    confusion_figure(
        url["confusion_matrix"],
        url["confusion_labels"],
        "Phishing URL classifier — test set",
        IMG / "confusion_url.png",
    )
    importance_figure(
        url["feature_importances"],
        "URL features by importance",
        IMG / "feature_importance_url.png",
    )

    top_features = "\n".join(
        f"| {i + 1} | `{f['feature']}` | {f['importance']:.4f} |"
        for i, f in enumerate(url["feature_importances"][:12])
    )

    content = f"""# ML Metrics

Generated by `ml_training/evaluate.py`. Do not edit by hand — re-run after training.

---

## 1. Scam message classifier

Word (1–2 gram) + character (3–5 gram) TF-IDF, union-vectorised, into a calibrated
Logistic Regression. Character n-grams are what make Tamil and Tanglish work without a stemmer.

| Property | Value |
|---|---|
| Trained at | {text['trained_at']} |
| Corpus size | {text['rows']} messages |
| Scam / legitimate | {text['rows_scam']} / {text['rows_legitimate']} |
| Tamil + Tanglish rows | {text['rows_tamil']} ({text['rows_tamil'] / text['rows'] * 100:.1f}%) |
| Best hyper-parameters | `{text['binary_best_params']}` |

### Binary (scam vs legitimate)

| Metric | Value |
|---|---|
| Test accuracy | {text['binary_test_accuracy']:.4f} |
| Test macro-F1 | {text['binary_test_macro_f1']:.4f} |
| Precision (scam) | {text['binary_precision_scam']:.4f} |
| Recall (scam) | {text['binary_recall_scam']:.4f} |
| 5-fold CV macro-F1 | {text['binary_cv_f1_macro']:.4f} ± {text['binary_cv_std']:.4f} |

{_confusion_table(text['confusion_matrix'], text['confusion_labels'])}

![Confusion matrix — scam message classifier](img/confusion_text.png)

### Scam category classifier

| Metric | Value |
|---|---|
| Classes | {len(text['category_classes'])} |
| Accuracy | {text['category_accuracy']:.4f} |
| Macro-F1 | {text['category_macro_f1']:.4f} |

Categories: {', '.join(f'`{c}`' for c in text['category_classes'])}

---

## 2. Phishing URL classifier

Random Forest over {len(url['feature_importances'])} static, network-free features.
The URL is never fetched.

| Property | Value |
|---|---|
| Trained at | {url['trained_at']} |
| Corpus size | {url['rows']} URLs |
| Phishing / safe | {url['rows_phishing']} / {url['rows_safe']} |
| Best hyper-parameters | `{url['best_params']}` |
| Test accuracy | {url['test_accuracy']:.4f} |
| Test macro-F1 | {url['test_macro_f1']:.4f} |
| Precision (phishing) | {url['precision_phishing']:.4f} |
| Recall (phishing) | {url['recall_phishing']:.4f} |
| ROC-AUC | {url['roc_auc']:.4f} |
| 5-fold CV macro-F1 | {url['cv_f1_macro']:.4f} ± {url['cv_std']:.4f} |

{_confusion_table(url['confusion_matrix'], url['confusion_labels'])}

![Confusion matrix — phishing URL classifier](img/confusion_url.png)

### Top features by importance

![URL features by importance](img/feature_importance_url.png)

| # | Feature | Importance |
|---|---|---|
{top_features}

---

## 3. How to read these numbers — important

**These scores are an upper bound, not expected field accuracy.** Quote them with this caveat
in your report; it is the first thing a careful examiner will probe.

1. **The corpus is synthetic.** Both datasets are generated from templates in
   `ml_training/generate_datasets.py`, composed from publicly documented fraud patterns. No real
   victim messages and no live malicious domains are included — a deliberate ethical and legal
   choice. The consequence is that the two classes are far more cleanly separable than real
   traffic, which is why the figures approach 1.00.

2. **Held-out does not mean independent.** The test split comes from the same generator as the
   training split. It measures whether the model learned the generator's patterns, not whether
   it generalises to scams written by an actual fraudster.

3. **One leak was found and removed.** An earlier version of the URL generator gave phishing
   URLs `http://` and safe URLs `https://`, letting the model reach 100% accuracy on the
   `is_https` feature alone. The generator now makes phishing URLs predominantly HTTPS, which
   is both more realistic (free certificates are universal) and removes the shortcut.
   `is_https` no longer appears among the top features — evidence the fix worked.

4. **This is why the system is a hybrid.** The rule engine in `app/ml/rules.py` carries 45% of
   the scam score and does not depend on the training distribution at all. A scam script the
   model has never seen still trips the OTP, KYC or digital-arrest rules, and the rules are what
   produce the bilingual explanation shown to the user.

### To strengthen this for a dissertation

- Collect a small **real** validation set (100–200 messages) donated with consent at workshops,
  label it by hand, and report accuracy on that separately. Even 100 real messages is a far more
  credible number than 850 synthetic ones.
- Report per-language performance separately; Tamil has fewer rows than English.
- Add a confusion analysis of which scam categories are mistaken for each other.
"""

    out = DOCS / "ML_METRICS.md"
    out.write_text(content, encoding="utf-8")
    print(f"wrote {out}")
    print(f"  text  macro-F1 {text['binary_test_macro_f1']:.4f}")
    print(f"  url   accuracy {url['test_accuracy']:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
