from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "TB_FUTURES_SOP.md"
OUTPUT = ROOT / "docs" / "TB_FUTURES_SOP.pdf"


def escape(text: str) -> str:
    return html.escape(text, quote=False)


def normalize_inline_markdown(text: str) -> str:
    text = escape(text)
    text = re.sub(r"`([^`]+)`", r"<font face='Courier'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="DocTitle",
            parent=styles["Title"],
            fontName="Times-Bold",
            fontSize=22,
            leading=26,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1A1A1A"),
            spaceAfter=18,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#222222"),
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2",
            parent=styles["Heading2"],
            fontName="Times-Bold",
            fontSize=15,
            leading=18,
            textColor=colors.HexColor("#1A1A1A"),
            spaceBefore=10,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="H3",
            parent=styles["Heading3"],
            fontName="Times-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#1A1A1A"),
            spaceBefore=8,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletItem",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#222222"),
            leftIndent=14,
            firstLineIndent=-8,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="NumberItem",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor("#222222"),
            leftIndent=14,
            firstLineIndent=-14,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="CodeLabel",
            parent=styles["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=9.5,
            leading=12,
            textColor=colors.HexColor("#444444"),
            spaceBefore=4,
            spaceAfter=4,
        )
    )
    return styles


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawRightString(doc.pagesize[0] - 0.75 * inch, 0.55 * inch, f"Page {doc.page}")
    canvas.restoreState()


def parse_markdown(lines: list[str]):
    styles = build_styles()
    story = []
    paragraph_buffer: list[str] = []
    code_buffer: list[str] = []
    in_code_block = False

    def flush_paragraph():
        nonlocal paragraph_buffer
        if not paragraph_buffer:
            return
        text = " ".join(chunk.strip() for chunk in paragraph_buffer).strip()
        if text:
            story.append(Paragraph(normalize_inline_markdown(text), styles["Body"]))
        paragraph_buffer = []

    def flush_code():
        nonlocal code_buffer
        if not code_buffer:
            return
        story.append(Paragraph("Command block", styles["CodeLabel"]))
        story.append(
            Preformatted(
                "\n".join(code_buffer),
                ParagraphStyle(
                    "CodeBlock",
                    fontName="Courier",
                    fontSize=9,
                    leading=12,
                    leftIndent=12,
                    rightIndent=12,
                    backColor=colors.HexColor("#F4F0EB"),
                    borderColor=colors.HexColor("#E3DDD5"),
                    borderWidth=0.5,
                    borderPadding=8,
                    spaceAfter=10,
                ),
            )
        )
        code_buffer = []

    for raw_line in lines:
        line = raw_line.rstrip("\n")
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_paragraph()
            if in_code_block:
                flush_code()
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_buffer.append(line)
            continue

        if not stripped:
            flush_paragraph()
            continue

        if stripped == "---":
            flush_paragraph()
            story.append(Spacer(1, 8))
            continue

        if stripped.startswith("# "):
            flush_paragraph()
            story.append(Paragraph(normalize_inline_markdown(stripped[2:].strip()), styles["DocTitle"]))
            continue

        if stripped.startswith("## "):
            flush_paragraph()
            story.append(Paragraph(normalize_inline_markdown(stripped[3:].strip()), styles["H2"]))
            continue

        if stripped.startswith("### "):
            flush_paragraph()
            story.append(Paragraph(normalize_inline_markdown(stripped[4:].strip()), styles["H3"]))
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            story.append(Paragraph(f"- {normalize_inline_markdown(stripped[2:].strip())}", styles["BulletItem"]))
            continue

        if re.match(r"^\d+\.\s+", stripped):
            flush_paragraph()
            story.append(Paragraph(normalize_inline_markdown(stripped), styles["NumberItem"]))
            continue

        paragraph_buffer.append(stripped)

    flush_paragraph()
    flush_code()
    return story


def main():
    lines = SOURCE.read_text(encoding="utf-8").splitlines(keepends=True)
    story = parse_markdown(lines)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=LETTER,
        leftMargin=0.8 * inch,
        rightMargin=0.8 * inch,
        topMargin=0.8 * inch,
        bottomMargin=0.8 * inch,
        title="TB Futures Product SOP and Design History",
        author="TB Futures",
    )
    doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()
