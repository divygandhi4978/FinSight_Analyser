#!/usr/bin/env python3
"""
AI Investment Committee – Full Pipeline Runner (Auditable, Report-Grade)

PIPELINE:
Module 1 → Deterministic Business Overview
Module 1 → Financial Statements
Module 2 → Management Commentary (RAG)
Module 2 → News (Context Only)
Module 3 → Investment Committee (FULL REPORT)

ALL intermediate artifacts are saved to disk.

OUTPUT STRUCTURE:
output/
  ├── <COMPANY>_business_overview.json
  ├── <COMPANY>_financials.json
  ├── <COMPANY>_concall.json
  ├── <COMPANY>_news.json
  ├── <COMPANY>_IC_inputs.json
  └── <COMPANY>_IC_decision.json   ← AUTHORITATIVE REPORT
"""

import json
import os

# ============================================================
# CONFIG
# ============================================================

COMPANY_CODE = "CAMS"
SCREENER_URL = f"https://www.screener.in/company/{COMPANY_CODE}/consolidated/"
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# UTILS
# ============================================================

def save_json(filename: str, data: dict):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  💾 Saved: {path}")

# ============================================================
# MODULE 1 — BUSINESS OVERVIEW (DETERMINISTIC)
# ============================================================

from Module_1.BusinessOverview import get_business_overview

print("▶ Fetching deterministic business overview...")

business_overview = get_business_overview(COMPANY_CODE)

assert "plain_english_summary" in business_overview, "Business summary missing"
assert "confidence" in business_overview, "Business confidence missing"

save_json(
    f"{COMPANY_CODE}_business_overview.json",
    business_overview
)

print("✔ Business overview fetched")
print("  └ Confidence:", business_overview["confidence"])

# ============================================================
# MODULE 1 — FINANCIALS
# ============================================================

from Module_1.extract_screener_financials import get_company_snapshot

print("\n▶ Fetching financial statements...")

financials = get_company_snapshot(
    code=COMPANY_CODE,
    include_financials=True,
    include_overview=False
)

assert "financials" in financials, "Financials block missing"

save_json(
    f"{COMPANY_CODE}_financials.json",
    financials
)

print("✔ Financials fetched")

# ============================================================
# MODULE 2 — MANAGEMENT COMMENTARY (RAG)
# ============================================================

from Module_2.concall_investor import get_future_plans_from_screener

print("\n▶ Fetching management commentary (concall / investor decks)...")

concall = get_future_plans_from_screener(SCREENER_URL)

assert "future_plans_and_calls" in concall, "Concall extraction failed"

save_json(
    f"{COMPANY_CODE}_concall.json",
    concall
)

print("✔ Management commentary fetched")

# ============================================================
# MODULE 2 — NEWS (CONTEXT ONLY)
# ============================================================

from Module_2.news_links import get_company_news

print("\n▶ Fetching news (context only)...")

news = get_company_news(
    company=COMPANY_CODE,
    limit=8,
    filter_authoritative=False
)

assert "news_count" in news and "news" in news, "News extraction failed"

save_json(
    f"{COMPANY_CODE}_news.json",
    news
)

print(f"✔ News fetched | Count: {news['news_count']}")

# ============================================================
# MODULE 3 — INVESTMENT COMMITTEE (FULL REPORT)
# ============================================================

from Module_3.Analyser import run_investment_committee

print("\n▶ Running Investment Committee (full report generation)...")

committee_output = run_investment_committee(
    company=COMPANY_CODE,
    b_overview=business_overview,
    financials=financials,
    concall=concall
)

assert "investment_report" in committee_output, "Invalid IC report output"

# ============================================================
# SAVE IC INPUTS (AUDIT TRAIL — CRITICAL)
# ============================================================

ic_inputs = {
    "company": COMPANY_CODE,

    "business_summary": business_overview["plain_english_summary"],
    "business_confidence": business_overview["confidence"],

    "decision_inputs": committee_output["decision_inputs"],
    "financial_signals": committee_output["financial_signals"],
    "owner_earnings": committee_output["owner_earnings"]
}

save_json(
    f"{COMPANY_CODE}_IC_inputs.json",
    ic_inputs
)

# ============================================================
# FINAL AUTHORITATIVE OUTPUT (DO NOT RECONSTRUCT)
# ============================================================

final_output = {
    "company": COMPANY_CODE,
    "generated_at": committee_output["generated_at"],

    # FULL REPORT FROM MODULE-3 (SOURCE OF TRUTH)
    "investment_report": committee_output["investment_report"],

    # Context only — explicitly NOT used in decision
    "news_context": {
        "news_count": news["news_count"],
        "sample_headlines": [
            n["title"] for n in news["news"][:3]
        ]
    }
}

save_json(
    f"{COMPANY_CODE}_IC_decision.json",
    final_output
)

# ============================================================
# CONSOLE SUMMARY
# ============================================================

decision_block = final_output["investment_report"]["committee_decision"]

print("\n✅ INVESTMENT COMMITTEE PIPELINE COMPLETE")
print("\n=== FINAL VERDICT ===")
print("Decision  :", decision_block["final_decision"])
print("Confidence:", decision_block["confidence"])

from Module_4.report import generate_ic_pdf
# ============================================================
# PDF REPORT GENERATION (FINAL ARTIFACT)
# ============================================================

print("\n▶ Generating Investment Committee PDF report...")

ic_decision_path = os.path.join(
    OUTPUT_DIR,
    f"{COMPANY_CODE}_IC_decision.json"
)

pdf_path = generate_ic_pdf(ic_decision_path)

print(f"✔ IC PDF generated: {pdf_path}")
