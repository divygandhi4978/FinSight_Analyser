#!/usr/bin/env python3
"""
Module-3: AI Investment Committee Simulator
Deterministic + Explainable + Decision-First

This module FORCES:
- A Buy / Hold / Avoid decision
- Explicit scoring logic
- Clear failure conditions
"""

import os
import json
from datetime import datetime
from groq import Groq

# ============================================================
# CONFIG
# ============================================================

MODEL = "llama-3.1-8b-instant"
TEMPERATURE = 0.0
MAX_TOKENS = 1600
RETRIES = 2

MAX_TEXT_CHARS = 1000

# ============================================================
# UTILS
# ============================================================

def clip(text, limit=MAX_TEXT_CHARS):
    return text[:limit] if text else ""

def safe_div(a, b):
    return round(a / b, 2) if b else "NA"

# ============================================================
# SCHEMA RESOLUTION
# ============================================================

def resolve_financial_block(financials):
    block = financials["financials"]["financials"]
    required = {"profit_and_loss", "balance_sheet", "cash_flows"}
    if not required.issubset(block.keys()):
        raise RuntimeError("Invalid financial schema")
    return block

# ============================================================
# DETERMINISTIC SIGNAL EXTRACTION
# ============================================================

def compute_core_signals(pnl, bs, cf):
    revenue = pnl.get("sales", 0)
    net_profit = pnl.get("net_profit", 0)
    op_margin = pnl.get("operating_margin", "NA")

    debt = bs.get("total_debt", 0)
    equity = bs.get("equity", 0)
    d_e = safe_div(debt, equity)

    op_cf = cf.get("operating_cash_flow", 0)
    capex = cf.get("capex", 0)

    return {
        "revenue": revenue,
        "net_profit": net_profit,
        "operating_margin": op_margin,
        "debt_to_equity": d_e,
        "operating_cash_flow": op_cf,
        "capex": capex
    }

# ============================================================
# ECONOMIC EARNINGS (OWNER VIEW)
# ============================================================

def compute_owner_earnings(pnl, cf):
    depreciation = pnl.get("depreciation", 0)
    op_cf = cf.get("operating_cash_flow", 0)

    maintenance_capex = depreciation * 0.6
    owner_earnings = op_cf - maintenance_capex

    return {
        "owner_earnings": round(owner_earnings, 2),
        "maintenance_capex_estimate": round(maintenance_capex, 2)
    }

# ============================================================
# DECISION INPUT NORMALIZATION (CRITICAL)
# ============================================================

def normalize_decision_inputs(signals):
    """
    Convert messy reality → bounded 0–1 decision inputs.
    Hard logic. No ML. Interview-safe.
    """

    def score_margin(m):
        if m == "NA": return 0.5
        if m > 20: return 0.85
        if m > 15: return 0.7
        if m > 10: return 0.55
        return 0.3

    def score_leverage(d):
        if d == "NA": return 0.5
        if d < 0.5: return 0.85
        if d < 1.0: return 0.65
        if d < 1.5: return 0.45
        return 0.25

    return {
        "business_quality": score_margin(signals["operating_margin"]),
        "financial_resilience": score_leverage(signals["debt_to_equity"]),
        "capital_discipline": 0.6 if signals["capex"] > 0 else 0.4,
        "cash_generation": 0.7 if signals["operating_cash_flow"] > 0 else 0.3
    }

# ============================================================
# LLM PAYLOAD (TOKEN-SAFE)
# ============================================================

def build_llm_payload(b_overview, concall, decision_inputs, signals, owner_earnings):
    return {
        "business_overview": clip(b_overview.get("overview", "")),
        "management_commentary": clip(concall.get("future_plans_and_calls", "")),

        "decision_inputs": decision_inputs,
        "financial_signals": signals,
        "owner_earnings": owner_earnings,

        "instructions": {
            "note_on_data": "Zero or NA values indicate missing or incomplete data, not economic zero. Interpret cautiously."
        }
    }

# ============================================================
# PROMPT (THIS IS THE DIFFERENCE)
# ============================================================
def build_prompt(company, payload):
    return f"""
You are an AI Investment Committee preparing a FULL INVESTMENT REPORT.

Your responsibilities:
- Interpret business fundamentals
- Explain financial ambiguity
- Take a BUY / HOLD / AVOID decision
- Clearly state what would change the decision

STRICT RULES:
- DO NOT calculate new numbers
- DO NOT invent facts
- Use ONLY provided inputs
- Treat 0 / NA as missing data
- Scores are already computed (0–1)
- Output VALID JSON ONLY
- Be detailed, analytical, and report-grade

INPUT:
{json.dumps(payload, indent=2)}

OUTPUT JSON SCHEMA (MANDATORY):
{{
  "company": "{company}",
  "decision_timestamp": "{datetime.utcnow().isoformat()}Z",

  "business_overview": {{
    "long_description": "",
    "business_model": {{
      "revenue_streams": [],
      "cost_structure": []
    }},
    "competitive_positioning": {{
      "strengths": [],
      "weaknesses": []
    }}
  }},

  "financial_interpretation": {{
    "data_quality_assessment": "",
    "profitability_insight": "",
    "leverage_and_balance_sheet_view": "",
    "cash_flow_view": ""
  }},

  "decision_inputs_summary": {{
    "business_quality": 0.0,
    "financial_resilience": 0.0,
    "capital_discipline": 0.0,
    "cash_generation": 0.0,
    "interpretation": ""
  }},

  "investment_thesis": {{
    "bull_case": [],
    "bear_case": [],
    "base_case": ""
  }},

  "committee_decision": {{
    "final_decision": "BUY | HOLD | AVOID",
    "confidence": 0.0,
    "decision_drivers": [
      {{
        "factor": "",
        "impact": "+ | -",
        "rationale": ""
      }}
    ],
    "decision_breakers": [],
    "required_assumptions": [],
    "committee_summary": ""
  }},

  "monitoring_triggers": {{
    "upgrade_to_buy_if": [],
    "downgrade_to_avoid_if": []
  }}
}}
"""

# ============================================================
# EXECUTOR
# ============================================================

def run_investment_committee(company, b_overview, financials, concall):

    block = resolve_financial_block(financials)

    signals = compute_core_signals(
        block["profit_and_loss"],
        block["balance_sheet"],
        block["cash_flows"]
    )

    owner_earnings = compute_owner_earnings(
        block["profit_and_loss"],
        block["cash_flows"]
    )

    decision_inputs = normalize_decision_inputs(signals)

    payload = build_llm_payload(
        b_overview=b_overview,
        concall=concall,
        decision_inputs=decision_inputs,
        signals=signals,
        owner_earnings=owner_earnings
    )
    prompt = build_prompt(company, payload)

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    for attempt in range(RETRIES):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )

        raw = response.choices[0].message.content.strip()

# ---------- HARD JSON SANITIZATION ----------
        if raw.startswith("```"):
            raw = raw.strip("`")
            raw = raw.replace("json\n", "", 1).strip()

        try:
            decision = json.loads(raw)
            return {
                "company": company,
                "generated_at": datetime.now().isoformat(),
                "decision_inputs": decision_inputs,
                "financial_signals": signals,
                "owner_earnings": owner_earnings,
                "investment_report": decision
            }
        except json.JSONDecodeError:
            if attempt == RETRIES - 1:
                raise RuntimeError(f"INVALID JSON OUTPUT:\n{raw}")
