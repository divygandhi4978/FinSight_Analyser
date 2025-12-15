#!/usr/bin/env python3
"""
Full Equity Analysis Pipeline
=============================

This script orchestrates:
- Module 1: Business Overview + Financials
- Module 2: Concall insights + News
- Module 3: Equity analysis synthesis

Company is controlled by a SINGLE variable: COMPANY_CODE

Output:
- <COMPANY_CODE>_equity_analysis.json
"""

import json
import sys

# ============================================================
# CONFIG
# ============================================================

# COMPANY_CODE = "NTPCGREEN"
# COMPANY_CODE = "ADANIPORTS"
# COMPANY_CODE = "ITCHOTELS"
# COMPANY_CODE = "LEMONTREE"
# COMPANY_CODE = "MAXHEALTH"
COMPANY_CODE = "EMBASSY"
SCREENER_URL = f"https://www.screener.in/company/{COMPANY_CODE}/consolidated/"

# ============================================================
# MODULE 1 – BUSINESS OVERVIEW & FINANCIALS
# ============================================================

from Module_1.BusinessOverview import get_business_overview
from Module_1.extract_screener_financials import get_company_snapshot

print("🔹 Fetching Business Overview...")

b_overview = get_business_overview(
    code=COMPANY_CODE,
    provider="groq",
    top_k=3
)

# Basic sanity checks
assert "overview" in b_overview, "Business overview missing"
assert "missing_headings" in b_overview, "Missing headings key not found"

print("✔ Business Overview fetched")
print("Missing headings:", b_overview["missing_headings"])

print("\n🔹 Fetching Financials...")

financials = get_company_snapshot(
    code=COMPANY_CODE,
    include_financials=True,
    include_overview=False  # IMPORTANT: overview already fetched above
)

# Validate structure early (fail fast)
assert "financials" in financials, "Financials block missing"
assert "financials" in financials["financials"], "Nested financials missing"

print("✔ Financials fetched")
print("Available sections:",
      financials["financials"]["financials"].keys())

# ============================================================
# MODULE 2 – CONCALL & NEWS
# ============================================================

from Module_2.concall_investor import get_future_plans_from_screener
from Module_2.news_links import get_company_news

print("\n🔹 Fetching Concall / Management Commentary...")

concall = get_future_plans_from_screener(SCREENER_URL)

assert "company" in concall, "Concall company key missing"
assert "future_plans_and_calls" in concall, "Concall insights missing"

print("✔ Concall data fetched for:", concall["company"])

print("\n🔹 Fetching News...")

news = get_company_news(
    company=COMPANY_CODE,
    limit=8,
    filter_authoritative=False  # set True only if you want strict filtering
)

assert "news_count" in news, "News count missing"
assert "news" in news, "News list missing"

print(f"✔ News fetched | Count: {news['news_count']}")

if news["news"]:
    print("Top headline:", news["news"][0]["title"])
else:
    print("⚠ No news found")

# ============================================================
# MODULE 3 – EQUITY ANALYSIS ENGINE
# ============================================================

from Module_3.Analyser import run_module_3

print("\n🔹 Running Module-3 Equity Analysis Engine...")

analysis = run_module_3(
    company=COMPANY_CODE,
    b_overview=b_overview,
    financials=financials,
    concall=concall
    # news=news   # ← you were NOT passing news earlier; that was a logic hole
)

assert isinstance(analysis, dict), "Final analysis must be a dict"

# ============================================================
# OUTPUT
# ============================================================

output_file = f"{COMPANY_CODE}_equity_analysis.json"

with open(output_file, "w", encoding="utf-8") as f:
    json.dump(analysis, f, indent=2, ensure_ascii=False)

print("\n✅ Analysis completed successfully")
print(f"📄 Output saved to: {output_file}")
