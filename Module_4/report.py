import json
import os

from jinja2 import Template

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# =========================================================
# PATH RESOLUTION (ROBUST)
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================================================
# HTML GENERATOR
# =========================================================
def generate_html(data: dict) -> str:
    template_path = os.path.join(TEMPLATE_DIR, "report.html")

    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    html_content = template.render(data=data)

    output_path = os.path.join(OUTPUT_DIR, f"{data['company']}_report.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return output_path


# =========================================================
# PDF GENERATOR (PROFESSIONAL STYLING)
# =========================================================
def generate_pdf(data: dict) -> str:
    pdf_path = os.path.join(OUTPUT_DIR, f"{data['company']}_report.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    base_styles = getSampleStyleSheet()
    story = []

    # -------------------------
    # STYLES
    # -------------------------
    TITLE_STYLE = ParagraphStyle(
        name="TitleStyle",
        parent=base_styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=16
    )

    SECTION_STYLE = ParagraphStyle(
        name="SectionStyle",
        fontSize=13,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=8
    )

    BODY_STYLE = ParagraphStyle(
        name="BodyStyle",
        fontSize=10.5,
        leading=14,
        textColor=colors.HexColor("#1f2937"),
        spaceAfter=6
    )

    # -------------------------
    # TITLE
    # -------------------------
    story.append(
        Paragraph(
            f"{data['company']} – Equity Research Report",
            TITLE_STYLE
        )
    )
    story.append(Spacer(1, 12))

    # -------------------------
    # SECTION RENDERER
    # -------------------------
    def section_block(title: str, content: dict, bg_color):
        table_data = []

        # Section header
        table_data.append([
            Paragraph(title, SECTION_STYLE)
        ])

        # Section body
        for key, value in content.items():
            if isinstance(value, list):
                value = ", ".join(value)

            text = f"<b>{key.replace('_', ' ').title()}:</b> {value}"
            table_data.append([
                Paragraph(text, BODY_STYLE)
            ])

        table = Table(table_data, colWidths=[doc.width])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), bg_color),
            ("BOX", (0, 0), (-1, -1), 0.6, colors.lightgrey),
            ("INNERPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))

        story.append(table)
        story.append(Spacer(1, 14))

    # -------------------------
    # SECTIONS (LIGHT, PROFESSIONAL SHADING)
    # -------------------------
    section_block(
        "Business Fundamentals",
        data["business_fundamentals"],
        colors.HexColor("#fbfbfc")
    )

    section_block(
        "Financial Quality",
        data["financial_quality"],
        colors.HexColor("#f6f8fa")
    )

    section_block(
        "Moat & Competition",
        data["moat_and_competition"],
        colors.HexColor("#fbfbfc")
    )

    section_block(
        "Management & Guidance",
        data["management_and_concall"],
        colors.HexColor("#f6f8fa")
    )

    section_block(
        "Sector View",
        data["sector_view"],
        colors.HexColor("#fbfbfc")
    )

    section_block(
        "Risk Summary",
        data["risk_summary"],
        colors.HexColor("#f6f8fa")
    )

    section_block(
        "Final View",
        data["final_view"],
        colors.HexColor("#fbfbfc")
    )

    doc.build(story)
    return pdf_path


# =========================================================
# DRIVER (JSON FILE)
# =========================================================
def generate_reports(json_path: str):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    html = generate_html(data)
    pdf = generate_pdf(data)

    print("Generated:")
    print(html)
    print(pdf)


# =========================================================
# EXTERNAL CALLER SUPPORT
# =========================================================
def generate_reports_from_data(data: dict) -> dict:
    return {
        "html_path": generate_html(data),
        "pdf_path": generate_pdf(data)
    }


if __name__ == "__main__":
    generate_reports("ntpcgreen.json")
