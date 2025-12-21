#!/usr/bin/env python3
import json
import os

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
# CONFIG
# =========================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "../output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================================================
# PDF GENERATOR
# =========================================================
def generate_ic_pdf(json_path: str) -> str:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    report = data["investment_report"]
    company = report["company"]

    pdf_path = os.path.join(OUTPUT_DIR, f"{company}_IC_report.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=48,
        bottomMargin=48
    )

    styles = getSampleStyleSheet()
    story = []

    TITLE = ParagraphStyle(
        "TITLE",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#e5e7eb"),
        spaceAfter=16
    )

    SECTION = ParagraphStyle(
        "SECTION",
        fontSize=14,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#38bdf8"),
        spaceAfter=10
    )

    BODY = ParagraphStyle(
        "BODY",
        fontSize=10.8,
        leading=15,
        textColor=colors.HexColor("#e5e7eb"),
        spaceAfter=6
    )

    MUTED = ParagraphStyle(
        "MUTED",
        fontSize=10,
        textColor=colors.HexColor("#94a3b8"),
        spaceAfter=6
    )

    # =====================================================
    # BACKGROUND
    # =====================================================
    def dark_bg(canvas, _):
        canvas.setFillColor(colors.HexColor("#020617"))
        canvas.rect(0, 0, A4[0], A4[1], stroke=0, fill=1)

    # =====================================================
    # CARD HELPER
    # =====================================================
    def card(title, lines):
        story.append(Paragraph(title, SECTION))
        content = []
        for line in lines:
            content.append(Paragraph(line, BODY))
            content.append(Spacer(1, 4))

        table = Table([[content]], colWidths=[doc.width])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#020617")),
            ("BOX", (0,0), (-1,-1), 0.6, colors.HexColor("#1e293b")),
            ("INNERPADDING", (0,0), (-1,-1), 14),
        ]))

        story.append(table)
        story.append(Spacer(1, 22))

    # =====================================================
    # HEADER
    # =====================================================
    story.append(Paragraph(f"{company} — Investment Committee Memo", TITLE))
    story.append(Paragraph(
        f"Decision Timestamp: {report['decision_timestamp']}",
        MUTED
    ))
    story.append(Spacer(1, 18))

    # =====================================================
    # BUSINESS OVERVIEW
    # =====================================================
    bo = report["business_overview"]
    card("Business Overview", [
        bo["long_description"],
        f"<b>Revenue Streams:</b> {', '.join(bo['business_model']['revenue_streams'])}",
        f"<b>Cost Structure:</b> {', '.join(bo['business_model']['cost_structure'])}",
        f"<b>Strengths:</b> {', '.join(bo['competitive_positioning']['strengths'])}",
        f"<b>Weaknesses:</b> {', '.join(bo['competitive_positioning']['weaknesses'])}",
    ])

    # =====================================================
    # FINANCIAL INTERPRETATION
    # =====================================================
    fi = report["financial_interpretation"]
    card("Financial Interpretation", [
        fi["data_quality_assessment"],
        fi["profitability_insight"],
        fi["leverage_and_balance_sheet_view"],
        fi["cash_flow_view"],
    ])

    # =====================================================
    # DECISION INPUTS
    # =====================================================
    di = report["decision_inputs_summary"]
    card("Decision Inputs Summary", [
        f"Business Quality: {di['business_quality']}",
        f"Financial Resilience: {di['financial_resilience']}",
        f"Capital Discipline: {di['capital_discipline']}",
        f"Cash Generation: {di['cash_generation']}",
        di["interpretation"],
    ])

    # =====================================================
    # INVESTMENT THESIS
    # =====================================================
    it = report["investment_thesis"]
    card("Investment Thesis", [
        f"<b>Bull Case:</b> {' '.join(it['bull_case'])}",
        f"<b>Base Case:</b> {it['base_case']}",
        f"<b>Bear Case:</b> {' '.join(it['bear_case'])}",
    ])

    # =====================================================
    # COMMITTEE DECISION
    # =====================================================
    cd = report["committee_decision"]

    drivers = " ".join(
        f"{d['factor']} ({d['impact']}): {d['rationale']}"
        for d in cd["decision_drivers"]
    ) or "None"

    card("Committee Decision", [
        f"<b>Final Decision:</b> {cd['final_decision']}",
        f"<b>Confidence:</b> {cd['confidence']}",
        f"<b>Decision Drivers:</b> {drivers}",
        f"<b>Committee Summary:</b> {cd['committee_summary']}",
    ])

    # =====================================================
    # MONITORING TRIGGERS
    # =====================================================
    mt = report["monitoring_triggers"]
    card("Monitoring Triggers", [
        f"<b>Upgrade to BUY if:</b> {' '.join(mt['upgrade_to_buy_if'])}",
        f"<b>Downgrade to AVOID if:</b> {' '.join(mt['downgrade_to_avoid_if'])}",
    ])

    # =====================================================
    # NEWS CONTEXT (NON-DECISION)
    # =====================================================
    if "news_context" in data:
        nc = data["news_context"]
        card("News Context (Non-Decision)", nc["sample_headlines"])

    doc.build(story, onFirstPage=dark_bg, onLaterPages=dark_bg)
    return pdf_path

# =========================================================
# CLI
# =========================================================
if __name__ == "__main__":
    path = os.path.join("../output", "MAXHEALTH_IC_decision.json")
    print("Generated:", generate_ic_pdf(path))
