"""Convert Markdown content into a branded PDF report."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Iterable, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (  # type: ignore
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from markdown import markdown
from bs4 import BeautifulSoup


BODY_FONT = "Helvetica"
HEADER_FONT = "Helvetica-Bold"


def _markdown_to_paragraphs(markdown_text: str) -> Iterable[Paragraph]:
    html = markdown(markdown_text)
    soup = BeautifulSoup(html, "html.parser")
    styles = getSampleStyleSheet()
    styles["Normal"].fontName = BODY_FONT
    styles["Normal"].fontSize = 11
    styles["Heading1"].fontName = HEADER_FONT
    styles["Heading1"].fontSize = 20
    styles.add(ParagraphStyle(name="Heading2", parent=styles["Heading1"], fontSize=16))

    for element in soup.children:
        if getattr(element, "name", None) is None:
            continue
        if element.name in {"h1", "h2", "h3"}:
            style_name = "Heading1" if element.name == "h1" else "Heading2"
            yield Paragraph(element.get_text(), styles[style_name])
        elif element.name == "p":
            yield Paragraph(element.get_text(), styles["Normal"])
        elif element.name == "ul":
            for li in element.find_all("li"):
                yield Paragraph(f"• {li.get_text()}", styles["Normal"])
        yield Spacer(1, 0.15 * inch)


def build_pdf(
    output_path: Path,
    brand_name: str,
    brand_color: str,
    summary_markdown: str,
    raw_findings: List[tuple[str, str]],
    footer_text: str,
) -> Path:
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=60,
        bottomMargin=60,
        title=f"{brand_name} Smart Contract Audit",
    )

    elements: List = []

    header_style = ParagraphStyle(
        name="Header",
        fontName=HEADER_FONT,
        fontSize=22,
        textColor=brand_color,
        leading=26,
    )
    elements.append(Paragraph(brand_name, header_style))
    elements.append(Spacer(1, 0.2 * inch))

    metadata = [
        ["Report Generated", datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")],
        ["Automated Tools", "Slither, Mythril"],
    ]
    table = Table(metadata, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), BODY_FONT),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(brand_color)),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 0.25 * inch))

    elements.append(Paragraph("Executive Summary", header_style))
    elements.append(Spacer(1, 0.1 * inch))
    elements.extend(_markdown_to_paragraphs(summary_markdown))

    elements.append(Spacer(1, 0.2 * inch))
    elements.append(Paragraph("Detailed Findings", header_style))
    elements.append(Spacer(1, 0.1 * inch))

    for title, content in raw_findings:
        elements.append(Paragraph(title, ParagraphStyle(name="FindingTitle", fontName=HEADER_FONT, fontSize=14)))
        elements.extend(_markdown_to_paragraphs(content))

    def _footer(canvas, doc_):  # type: ignore
        canvas.saveState()
        canvas.setFont(BODY_FONT, 9)
        canvas.setFillColor(colors.grey)
        canvas.drawString(50, 40, footer_text)
        canvas.restoreState()

    doc.build(elements, onFirstPage=_footer, onLaterPages=_footer)
    return output_path


__all__ = ["build_pdf"]
