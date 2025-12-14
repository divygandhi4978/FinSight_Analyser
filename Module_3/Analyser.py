#!/usr/bin/env python3
"""
Module-3: Integrated Equity Research Engine (Single File)

INPUTS:
- b_overview  (dict)
- financials  (dict)
- concall     (dict)

OUTPUT:
- Valid structured JSON equity research report

LLM:
- Groq (llama-3.1-8b-instant)

FAILS HARD if JSON is invalid.
"""

import os
import json
from datetime import datetime
from groq import Groq

# ================= CONFIG =================

MODEL = "llama-3.1-8b-instant"
MAX_TOKENS = 2500
TEMPERATURE = 0.0
MAX_CHARS = 3000
RETRIES = 2

# ================= HELPERS =================

def clip(text, max_chars=MAX_CHARS):
    if not text:
        return ""
    return text[:max_chars]

def normalize_inputs(b_overview, financials, concall):
    """
    Reduce noise before sending to LLM
    """
    return {
        "business_overview": clip(b_overview.get("overview", "")),
        "missing_headings": b_overview.get("missing_headings", []),

        "ratios": financials.get("financials", {}).get("ratios", {}),
        "profit_and_loss": financials.get("financials", {}).get("profit_and_loss", {}),
        "balance_sheet": financials.get("financials", {}).get("balance_sheet", {}),
        "cash_flows": financials.get("financials", {}).get("cash_flows", {}),

        "concall_insights": clip(concall.get("future_plans_and_calls", ""))
    }

# ================= PROMPT =================

def build_prompt(company, data):
    return f"""
You are generating a FINAL BACKEND JSON DATA SOURCE
for a professional equity research web application.

CRITICAL OUTPUT RULE (NON-NEGOTIABLE):
- Output VALID JSON ONLY
- Do NOT include explanations, notes, markdown, or commentary
- Do NOT wrap JSON in ```json or ``` blocks
- The FIRST character must be '{' and the LAST character must be '}'
- If you violate this, the output is invalid

CRITICAL INSTRUCTIONS (NON-NEGOTIABLE):
1. Output STRICTLY VALID JSON ONLY.
2. This JSON is a BACKEND DATA CONTRACT for a web application.
3. Every descriptive STRING field MUST be a DETAILED ANALYTICAL PARAGRAPH.
4. Each paragraph MUST:
   - Be logically structured
   - Explain reasoning step-by-step
   - Reference business model, sector dynamics, and financial implications
5. ABSOLUTE MINIMUM LENGTH RULE:
   - Any descriptive text field < 80 words is INVALID.
   - If you cannot reach 80 words due to missing data, explain WHY and then write "NA".
6. NEVER use null.
7. NEVER invent numbers.
8. Use "NA" ONLY AFTER explaining data unavailability in words.
9. Do NOT repeat the same explanation across fields.
10. Think like a long-term equity investor, not a news analyst.

REASONING ENFORCEMENT RULE:
For EVERY classification you assign (pricing_power, moat_sustainability, capital_intensity, guidance_credibility, recommendation):
- You MUST explicitly justify WHY that classification was chosen.
- If justification is weak or data is missing, downgrade the classification.

INVESTMENT PHILOSOPHY OVERLAY:
Apply principles inspired by:
- Warren Buffett (moat, predictability, capital discipline)
- Rakesh Jhunjhunwala (growth + management quality)
- Vijay Kedia (sector tailwinds + scale potential)
- Ramdeo Agrawal (QGLP: Quality, Growth, Longevity, Price)

CONTENT DEPTH RULE (STRICT):
Each section should read like a **standalone analyst note**
that could be shown directly on an investor-facing webpage.
Shallow or generic text is considered FAILURE.

SCORING RULE (MANDATORY):
Conviction score (0–100):
- Start at 50
- +10 if ROCE > 15
- +10 if debt_to_equity < 1
- +10 if moat_sustainability = strong
- -10 if financial_risk = high
- -10 if guidance_credibility = low
Clamp between 0 and 100

VALUATION RULES:
- Use PE for asset-light businesses
- Use EV/EBITDA for capital-intensive businesses
- If insufficient data → valuation_range = "NA"

Also consider necessary parameter based on the company exists in which sector
Assume that you are financial analyst and adviser as top analyst and also some or more follow Warren Buffet , Rakesh Jhunjhunwala, Vijay Kedia , Ramdev Agarval strategy

COMPANY: {company}

INPUT DATA (SOURCE OF TRUTH):
{json.dumps(data, indent=2)}

OUTPUT JSON SCHEMA (FOLLOW EXACTLY):
{{
  "company": "{company}",
  "timestamp": "",

  "business_fundamentals": {{
    "what_the_company_does": "",
    "competitive_position": "",
    "pricing_power": "low | moderate | high | NA",
    "capital_intensity": "low | moderate | high | NA"
  }},

  "financial_quality": {{
    "roe": "NA",
    "roce": "NA",
    "debt_to_equity": "NA",
    "assessment": ""
  }},

  "moat_and_competition": {{
    "moat_sources": [],
    "moat_sustainability": "weak | moderate | strong | NA"
  }},

  "management_and_concall": {{
    "key_guidance_points": [],
    "execution_risks": [],
    "guidance_credibility": "low | moderate | high | NA"
  }},

  "sector_view": {{
    "sector_trend": "up | flat | down | NA",
    "tailwinds": [],
    "headwinds": []
  }},

  "valuation": {{
    "method_used": "PE | EV/EBITDA | NA",
    "bull_case": {{
      "assumptions": [],
      "valuation_range": "NA",
      "upside_pct": "NA"
    }},
    "base_case": {{
      "assumptions": [],
      "valuation_range": "NA",
      "upside_pct": "NA"
    }},
    "bear_case": {{
      "assumptions": [],
      "valuation_range": "NA",
      "downside_pct": "NA"
    }}
  }},

  "risk_summary": {{
    "business_risks": [],
    "financial_risks": [],
    "macro_risks": []
  }},

  "final_view": {{
    "recommendation": "strong_buy | buy | hold | avoid | sell",
    "conviction_score": 0,
    "key_reasons": [],
    "what_can_go_wrong": []
  }}
}}
"""

# ================= EXECUTOR =================

def run_module_3(company, b_overview, financials, concall):
    # client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    client = Groq(api_key="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") #API1
    client = Groq(api_key="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") #API1
    

    normalized = normalize_inputs(b_overview, financials, concall)
    prompt = build_prompt(company, normalized)

    for attempt in range(RETRIES):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )

        raw = response.choices[0].message.content.strip()

        try:
            parsed = json.loads(raw)
            parsed["company"] = company
            parsed["timestamp"] = datetime.now().isoformat()
            return parsed
        except json.JSONDecodeError:
            if attempt == RETRIES - 1:
                raise RuntimeError(f"Invalid JSON returned by LLM:\n{raw}")

# ================= USAGE EXAMPLE =================

if __name__ == "__main__":
    # These must already exist (from Module-1 & Module-2)
    # b_overview = ...
    # financials = ...
    # concall = ...

    analysis = run_module_3(
        company="LEMONTREE",
        b_overview=b_overview,
        financials=financials,
        concall=concall
    )

    print(json.dumps(analysis, indent=2))
