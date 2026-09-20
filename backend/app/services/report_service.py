"""Community-impact PDF report.

This is the artefact that goes into the Community Service Project appendix, so it states the
statistics *and* their caveats on the same page. A report that prints "87% average improvement"
without saying that the mean is skewed by low pre-test denominators invites exactly the question
it cannot answer.
"""

from __future__ import annotations

import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.services.certificate_service import TAMIL_FONT, _ensure_tamil_font

NAVY = colors.HexColor("#1e3a5f")
TEAL = colors.HexColor("#0f766e")
GREY = colors.HexColor("#475569")
LIGHT = colors.HexColor("#f1f5f9")
AMBER = colors.HexColor("#b45309")


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "title", parent=base["Title"], fontSize=20, textColor=NAVY, spaceAfter=4
        ),
        "subtitle": ParagraphStyle(
            "subtitle", parent=base["Normal"], fontSize=10.5, textColor=GREY,
            alignment=TA_CENTER, spaceAfter=14,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"], fontSize=13, textColor=NAVY,
            spaceBefore=14, spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"], fontSize=9.5, leading=14, textColor=colors.black
        ),
        "note": ParagraphStyle(
            "note", parent=base["Normal"], fontSize=8.5, leading=12.5, textColor=AMBER
        ),
        "small": ParagraphStyle(
            "small", parent=base["Normal"], fontSize=8, leading=11, textColor=GREY
        ),
    }


def _kv_table(rows: list[tuple[str, str]], width: float = 165 * mm) -> Table:
    table = Table([[k, v] for k, v in rows], colWidths=[width * 0.62, width * 0.38])
    table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME", (1, 0), (1, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
            ("TEXTCOLOR", (0, 0), (0, -1), GREY),
            ("TEXTCOLOR", (1, 0), (1, -1), NAVY),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT]),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    return table


def _grid_table(header: list[str], rows: list[list[str]], widths: list[float]) -> Table:
    table = Table([header, *rows], colWidths=widths, repeatRows=1)
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("ALIGN", (0, 0), (0, -1), "LEFT"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )
    return table


def _fmt(value, suffix: str = "", dash: str = "—") -> str:
    return dash if value is None else f"{value}{suffix}"


def build_impact_report(summary: dict, rows: list[dict]) -> bytes:
    """Render the dashboard summary and per-participant rows into a PDF."""
    has_tamil = _ensure_tamil_font()
    s = _styles()
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=22 * mm, rightMargin=22 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
        title="CyberSathi Community Impact Report", author="CyberSathi",
    )

    story = []
    a = summary["awareness"]
    totals = summary["totals"]

    # ----------------------------------------------------------------- header
    story.append(Paragraph("CyberSathi", s["title"]))
    story.append(Paragraph("Community Impact Report", s["subtitle"]))
    if has_tamil:
        story.append(Paragraph(
            f'<font name="{TAMIL_FONT}">சைபர் மோசடி விழிப்புணர்வு — சமூகத் தாக்க அறிக்கை</font>',
            s["subtitle"],
        ))
    story.append(Paragraph(f"Generated {date.today().isoformat()}", s["small"]))
    story.append(Spacer(1, 10))

    # ------------------------------------------------------------- reach
    story.append(Paragraph("1. Reach", s["h2"]))
    story.append(_kv_table([
        ("Workshops conducted", str(totals["workshops"])),
        ("Participants registered", str(totals["participants"])),
        ("Participants with matched pre and post tests", str(a["n_pairs"])),
        ("Messages checked through the analyzer", str(totals["messages_analyzed"])),
        ("Links checked", str(totals["urls_checked"])),
        ("Questions asked to the assistant", str(totals["assistant_queries"])),
    ]))

    # ------------------------------------------------------- awareness change
    story.append(Paragraph("2. Awareness change", s["h2"]))
    story.append(Paragraph(
        "Improvement is measured with matched pre- and post-tests: the same category profile, "
        "different questions, sampled deterministically per participant.",
        s["body"],
    ))
    story.append(Spacer(1, 6))
    story.append(_kv_table([
        ("Mean pre-test score", _fmt(a["avg_pre_pct"], "%")),
        ("Mean post-test score", _fmt(a["avg_post_pct"], "%")),
        ("Median improvement", _fmt(a["median_improvement_pct"], "%")),
        ("Mean improvement", _fmt(a["avg_improvement_pct"], "%")),
        ("Standard deviation of improvement", _fmt(a["std_dev_improvement"])),
        ("Moved from low awareness (<50%) to aware (>=70%)", _fmt(a["moved_to_aware_pct"], "%")),
    ]))

    # The caveat travels with the number, not in a footnote nobody reads.
    if a.get("interpretation_note"):
        note = a["interpretation_note"]
        text = note["en"] if isinstance(note, dict) else str(note)
        story.append(Spacer(1, 8))
        story.append(KeepTogether([
            Paragraph("<b>How to read the mean</b>", s["note"]),
            Paragraph(text, s["note"]),
        ]))

    # --------------------------------------------------------- the formula
    story.append(Paragraph("3. The improvement formula", s["h2"]))
    story.append(Paragraph(
        "Awareness Improvement = ((Post-test Score − Pre-test Score) / Pre-test Score) × 100",
        ParagraphStyle("formula", parent=s["body"], fontName="Courier-Bold",
                       fontSize=10, alignment=TA_CENTER, textColor=TEAL,
                       backColor=LIGHT, borderPadding=8, spaceBefore=4, spaceAfter=8),
    ))
    story.append(Paragraph(
        f"This expression is undefined when the pre-test score is zero, which occurred for "
        f"<b>{a['undefined_improvement_count']}</b> participant(s) — a realistic outcome for "
        f"first-time internet users. Those rows report <b>absolute gain</b> (post − pre) and "
        f"<b>normalized gain</b> (post − pre) / (max − pre), also called Hake's gain, instead of "
        f"a percentage. They are excluded from the mean and median improvement figures above and "
        f"counted here explicitly rather than silently dropped.",
        s["body"],
    ))

    # ------------------------------------------------- statistical significance
    story.append(Paragraph("4. Statistical significance", s["h2"]))
    p_value = a["p_value"]
    p_text = "< 0.001" if p_value is not None and p_value < 0.001 else _fmt(p_value)
    story.append(_kv_table([
        ("Paired-samples t-statistic", _fmt(a["t_statistic"])),
        ("Degrees of freedom (n − 1)", str(max(a["n_pairs"] - 1, 0))),
        ("p-value", p_text),
        ("Cohen's d (effect size)", _fmt(a["cohens_d"])),
        ("Matched pairs (n)", str(a["n_pairs"])),
    ]))
    d = a["cohens_d"]
    if d is not None:
        magnitude = "large" if abs(d) >= 0.8 else "medium" if abs(d) >= 0.5 else "small"
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            f"Interpretation: Cohen's d of {d} indicates a <b>{magnitude}</b> effect "
            f"(0.2 small, 0.5 medium, 0.8 and above large).",
            s["body"],
        ))

    story.append(PageBreak())

    # ------------------------------------------------------- category breakdown
    story.append(Paragraph("5. Awareness by scam category", s["h2"]))
    cat_rows = [
        [c["category"].replace("_", " ").title(), f"{c['pre']}%", f"{c['post']}%", f"{c['delta']:+.1f}"]
        for c in sorted(summary["improvement_by_category"], key=lambda x: -x["delta"])
    ]
    if cat_rows:
        story.append(_grid_table(
            ["Category", "Before", "After", "Change"],
            cat_rows, [70 * mm, 30 * mm, 30 * mm, 30 * mm],
        ))
    else:
        story.append(Paragraph("No category data yet.", s["small"]))

    # ---------------------------------------------------------- demographics
    for title, key, label in (
        ("6. Improvement by age group", "by_age_group", "Age group"),
        ("7. Improvement by district", "by_district", "District"),
        ("8. Improvement by language", "by_language", "Language"),
    ):
        groups = summary.get(key) or []
        if not groups:
            continue
        story.append(Paragraph(title, s["h2"]))
        story.append(_grid_table(
            [label, "n", "Before", "After", "Mean change"],
            [[g["group"].title(), str(g["n"]), f"{g['avg_pre']}%",
              f"{g['avg_post']}%", f"{g['avg_improvement']:+.1f}%"] for g in groups],
            [45 * mm, 20 * mm, 30 * mm, 30 * mm, 35 * mm],
        ))

    # -------------------------------------------------------------- activity
    story.append(Paragraph("9. What participants checked", s["h2"]))
    top = summary.get("top_scam_categories") or []
    if top:
        story.append(_grid_table(
            ["Scam type detected", "Count"],
            [[c["name"].replace("_", " ").title(), str(c["count"])] for c in top],
            [110 * mm, 50 * mm],
        ))
    risk = summary.get("risk_distribution") or {}
    if risk:
        story.append(Spacer(1, 8))
        story.append(_kv_table([
            ("Messages rated safe", str(risk.get("safe", 0))),
            ("Messages rated suspicious", str(risk.get("suspicious", 0))),
            ("Messages rated high risk", str(risk.get("high_risk", 0))),
        ]))

    feedback = summary.get("feedback") or {}
    if feedback.get("count"):
        story.append(Paragraph("10. Participant feedback", s["h2"]))
        story.append(_kv_table([
            ("Average session rating (out of 5)", str(feedback.get("avg_rating"))),
            ("Feedback responses collected", str(int(feedback.get("count", 0)))),
        ]))

    # ------------------------------------------------------------- appendix
    if rows:
        story.append(PageBreak())
        story.append(Paragraph("Appendix — per-participant results", s["h2"]))
        story.append(Paragraph(
            "Names are as recorded on the consent form. Phone numbers were never stored: the "
            "roster keeps only a one-way SHA-256 hash.",
            s["small"],
        ))
        story.append(Spacer(1, 6))

        appendix = []
        for r in rows:
            imp = r.get("improvement_percentage")
            change = f"{imp:+.1f}%" if imp is not None else f"+{r.get('absolute_gain', 0)} marks*"
            appendix.append([
                str(r.get("participant_id", "")),
                (r.get("name") or "")[:22],
                (r.get("age_group") or "")[:8],
                (r.get("district") or "")[:14],
                _fmt(r.get("pre_percentage"), "%"),
                _fmt(r.get("post_percentage"), "%"),
                change,
            ])

        story.append(_grid_table(
            ["ID", "Name", "Group", "District", "Pre", "Post", "Change"],
            appendix,
            [12 * mm, 38 * mm, 18 * mm, 28 * mm, 20 * mm, 20 * mm, 28 * mm],
        ))
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "* Percentage improvement is undefined when the pre-test score is zero; absolute "
            "gain in marks is shown for those participants.",
            s["small"],
        ))

    # --------------------------------------------------------------- footer
    story.append(Spacer(1, 14))
    story.append(Paragraph(
        "Cyber Crime Helpline 1930 &nbsp;·&nbsp; Report at cybercrime.gov.in<br/>"
        "Generated by CyberSathi. All analysis runs locally; no participant data leaves this machine.",
        s["small"],
    ))

    doc.build(story)
    return buffer.getvalue()
