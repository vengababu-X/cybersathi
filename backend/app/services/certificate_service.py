"""Bilingual PDF certificate generation.

Tamil in a PDF needs a font that actually contains the Tamil block. The standard reportlab
fonts do not, so we look for one in a few known locations and register it. If none is found the
certificate still generates — in English only, with a short note — rather than printing boxes.
Bundling Noto Sans Tamil in assets/fonts/ is the recommended fix and is documented in the README.
"""

from __future__ import annotations

import io
import logging
from datetime import date
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from app.config import BASE_DIR
from app.models import Participant, Workshop

logger = logging.getLogger(__name__)

TAMIL_FONT = "CyberSathiTamil"
_tamil_ready: bool | None = None

# (path, subfont index for .ttc collections)
_FONT_CANDIDATES: list[tuple[Path, int]] = [
    (BASE_DIR / "assets" / "fonts" / "NotoSansTamil-Regular.ttf", 0),
    (BASE_DIR.parent / "frontend" / "public" / "fonts" / "NotoSansTamil-Regular.ttf", 0),
    (Path("C:/Windows/Fonts/Nirmala.ttc"), 0),
    (Path("C:/Windows/Fonts/latha.ttf"), 0),
    (Path("/usr/share/fonts/truetype/noto/NotoSansTamil-Regular.ttf"), 0),
    (Path("/System/Library/Fonts/Supplemental/Tamil MN.ttc"), 0),
]


def _ensure_tamil_font() -> bool:
    global _tamil_ready
    if _tamil_ready is not None:
        return _tamil_ready

    for path, index in _FONT_CANDIDATES:
        if not path.exists():
            continue
        try:
            if path.suffix.lower() == ".ttc":
                pdfmetrics.registerFont(TTFont(TAMIL_FONT, str(path), subfontIndex=index))
            else:
                pdfmetrics.registerFont(TTFont(TAMIL_FONT, str(path)))
            logger.info("Tamil PDF font registered from %s", path)
            _tamil_ready = True
            return True
        except Exception:
            logger.debug("could not register font %s", path, exc_info=True)

    logger.warning("No Tamil-capable font found — certificates will be English only")
    _tamil_ready = False
    return False


def build_certificate(
    participant: Participant, workshop: Workshop | None, improvement: dict
) -> bytes:
    has_tamil = _ensure_tamil_font()
    buffer = io.BytesIO()
    width, height = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    navy = colors.HexColor("#1e3a5f")
    teal = colors.HexColor("#0f766e")
    grey = colors.HexColor("#475569")

    # Border
    c.setStrokeColor(navy)
    c.setLineWidth(3)
    c.rect(12 * mm, 12 * mm, width - 24 * mm, height - 24 * mm)
    c.setStrokeColor(teal)
    c.setLineWidth(1)
    c.rect(16 * mm, 16 * mm, width - 32 * mm, height - 32 * mm)

    # Header
    c.setFillColor(navy)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(width / 2, height - 38 * mm, "CyberSathi")
    c.setFont("Helvetica", 12)
    c.setFillColor(grey)
    c.drawCentredString(
        width / 2, height - 46 * mm, "Cyber-Fraud Awareness & Digital Safety Programme"
    )

    if has_tamil:
        c.setFont(TAMIL_FONT, 12)
        c.drawCentredString(width / 2, height - 53 * mm, "சைபர் மோசடி விழிப்புணர்வு திட்டம்")

    c.setFillColor(teal)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 68 * mm, "CERTIFICATE OF PARTICIPATION")

    # Name
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, height - 82 * mm, "This is to certify that")

    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(navy)
    c.drawCentredString(width / 2, height - 94 * mm, participant.name)

    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    venue = workshop.venue if workshop else "a community session"
    conducted = workshop.conducted_on if workshop else date.today()
    c.drawCentredString(
        width / 2,
        height - 104 * mm,
        f"participated in the cyber safety awareness workshop at {venue}",
    )
    c.drawCentredString(width / 2, height - 111 * mm, f"held on {conducted}")

    # Scores
    pre = improvement.get("pre_percentage")
    post = improvement.get("post_percentage")
    imp = improvement.get("improvement_percentage")
    gain = improvement.get("absolute_gain")

    box_y = 42 * mm
    c.setStrokeColor(teal)
    c.setFillColor(colors.HexColor("#f0fdfa"))
    c.roundRect(width / 2 - 85 * mm, box_y, 170 * mm, 26 * mm, 4, stroke=1, fill=1)

    c.setFillColor(grey)
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, box_y + 19 * mm, "AWARENESS ASSESSMENT RESULT")

    c.setFillColor(navy)
    c.setFont("Helvetica-Bold", 12)
    pre_text = f"Pre-test: {pre:.0f}%" if pre is not None else "Pre-test: —"
    post_text = f"Post-test: {post:.0f}%" if post is not None else "Post-test: —"

    if imp is not None:
        change_text = f"Improvement: {imp:+.1f}%"
    elif gain is not None:
        # Honest handling of the pre_score = 0 case rather than printing an infinity.
        change_text = f"Gain: +{gain} marks"
    else:
        change_text = "Improvement: —"

    c.drawCentredString(width / 2 - 55 * mm, box_y + 9 * mm, pre_text)
    c.drawCentredString(width / 2, box_y + 9 * mm, post_text)
    c.drawCentredString(width / 2 + 55 * mm, box_y + 9 * mm, change_text)

    # Footer
    c.setFillColor(grey)
    c.setFont("Helvetica", 9)
    c.drawString(30 * mm, 26 * mm, "Cyber Crime Helpline: 1930")
    c.drawString(30 * mm, 21 * mm, "Report at: cybercrime.gov.in")

    c.setFont("Helvetica", 9)
    c.drawRightString(width - 30 * mm, 26 * mm, "Facilitator")
    c.setStrokeColor(grey)
    c.line(width - 75 * mm, 31 * mm, width - 30 * mm, 31 * mm)

    if not has_tamil:
        c.setFont("Helvetica-Oblique", 7)
        c.setFillColor(colors.HexColor("#94a3b8"))
        c.drawCentredString(
            width / 2, 15 * mm,
            "Tamil text omitted: no Tamil font installed. See README to enable bilingual certificates.",
        )

    c.showPage()
    c.save()
    return buffer.getvalue()
