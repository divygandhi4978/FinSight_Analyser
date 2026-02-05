#!/usr/bin/env python3
"""
screener_future_plans.py
========================

Autonomous equity research insight extractor.

PIPELINE:
Screener → Concall + Investor Presentations (scraped)
→ Cache (./cache/)
→ PDF / HTML Text Extraction
→ Block Scoring → Trim Corpus
→ Groq LLM → 1-Page Maker-Insight JSON

Public API:
-----------
result = get_future_plans_from_screener(url)

Returns:
{
  "company": "...",
  "source": "...",
  "concall_available": true,
  "documents_used": [...],
  "future_plans_and_calls": {...}
}
"""

import os
import re
import json
import time
import hashlib
import requests
from io import BytesIO
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# PDF
try:
    import pdfplumber
    HAS_PDF = True
except:
    HAS_PDF = False

# LLM
from groq import Groq

# ============================== CONFIG ==============================

HEADERS = {"User-Agent": "ScreenerFuturePlans/1.0"}
CACHE_DIR = "./cache"
os.makedirs(CACHE_DIR, exist_ok=True)

MAX_DOCS = 6
MIN_TEXT_LEN = 600
MAX_CORPUS_LEN = 2800

KEYWORDS_FUTURE = [
    "future", "outlook", "guidance", "capex", "expansion",
    "pipeline", "growth", "trajectory", "demand", "FY", "next year"
]


# ============================== CACHE ===============================

def cache_path(url: str):
    h = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(CACHE_DIR, h)

def cached_fetch(url: str):
    path = cache_path(url)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    with open(path, "wb") as f:
        f.write(r.content)
    return r.content

# ============================== SCRAPER ============================

def fetch_html(url):
    return cached_fetch(url).decode("utf-8", errors="ignore")

def find_links(screener_url, keywords, max_links):
    soup = BeautifulSoup(fetch_html(screener_url), "lxml")
    links = []
    for a in soup.find_all("a", href=True):
        t = (a.get_text() or "").lower()
        h = a["href"].lower()
        if any(k in t or k in h for k in keywords):
            full = urljoin(screener_url, a["href"])
            if full not in links:
                links.append(full)
    return links[:max_links]

def find_concall_links(url):
    return find_links(url, ["concall", "conference", "transcript"], 3)

def find_presentation_links(url):
    return find_links(url, ["presentation"], 3)

# ============================== TEXT EXTRACTION =====================

def extract_pdf_text(url):
    if not HAS_PDF:
        return None
    try:
        data = cached_fetch(url)
        with pdfplumber.open(BytesIO(data)) as pdf:
            text = "\n".join((p.extract_text() or "") for p in pdf.pages)
        return text if len(text) >= MIN_TEXT_LEN else None
    except:
        return None

def extract_html_text(url):
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "lxml")
        for t in soup(["script", "style"]):
            t.decompose()
        text = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
        return text if len(text) >= MIN_TEXT_LEN else None
    except:
        return None

def load_doc(url, dtype):
    text = extract_pdf_text(url) if url.lower().endswith(".pdf") else extract_html_text(url)
    if not text:
        return None
    return {"url": url, "type": dtype, "text": text, "len": len(text)}

# ============================== SCORING =============================

def score_block(block):
    score = 0
    low = block.lower()
    for kw in KEYWORDS_FUTURE:
        if kw in low:
            score += 3
    nums = re.findall(r"\b\d{1,4}\b", low)
    score += min(len(nums), 3)
    return score

def extract_top_corpus(docs):
    blocks = []
    for d in docs:
        parts = d["text"].split("\n")
        for p in parts:
            p = p.strip()
            if not p or len(p) < 80:
                continue
            blocks.append({"text": p, "score": score_block(p), "src": d})
    top = sorted(blocks, key=lambda x: x["score"], reverse=True)[:40]
    corpus = "\n".join(b["text"] for b in top)[:MAX_CORPUS_LEN]
    return corpus, top


# ============================== LLM ================================

def call_llm(company, corpus):
    api = "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"
    if not api:
        raise RuntimeError("Missing environment variable: GROQ_API_KEY")
    client = Groq(api_key=api)
    prompt = fprompt = f"""
You are an equity analyst. You must extract ONLY quantifiable business facts. 
Reject generic language. Reject opinions. Reject vague text. Only extract if the corpus states it exactly.

RULES:
- Never summarize with soft phrases. Use metrics or return null.
- Extract CAGR, EBITDA margin %, ARR or ADR, debt, capacity, pipeline count, geography, dates, timelines, FY labels.
- If values are not in text, do NOT invent them.
- Prefer bullet-level atomic facts.

Return JSON ONLY in EXACT schema below. No text outside JSON.

Schema:
{{
 "analysis": {{
   "important_management_calls": [],
   "future_business_plans": [],   // must include metric + timeline or leave empty
   "expansion_pipeline": [],      // must include counts or assets
   "capex_plans": {{"mentioned": false, "details": []}},
   "management_guidance": [],     // must extract numeric guidance
   "key_risks_highlighted": [],
   "timeline_summary": []
 }},
 "plain_english_summary": {{
   "priority_actions_next_12_months": "",
   "where_capital_is_flowing": "",
   "success_dependency": "",
   "main_risk_trigger": "",
   "big_picture_outlook": ""
 }}
}}

CORPUS (SOURCE FACTS ONLY):
{corpus}
"""

    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=1000
    )
    out = r.choices[0].message.content.strip()
    try:
        return json.loads(out)
    except:
        return {"raw_llm_output": out}

# ============================== PUBLIC API ==========================

def get_future_plans_from_screener(url: str):
    company = url.rstrip("/").split("/")[-2].upper()
    concalls = find_concall_links(url)
    pres = find_presentation_links(url)
    all_links = concalls + pres

    if not all_links:
        return {
            "company": company,
            "source": url,
            "concall_available": False,
            "documents_used": [],
            "future_plans_and_calls": "Not disclosed"
        }

    docs = []
    for l in all_links[:MAX_DOCS]:
        d = load_doc(l, "concall" if l in concalls else "presentation")
        if d:
            docs.append(d)

    if not docs:
        return {
            "company": company,
            "source": url,
            "concall_available": False,
            "documents_used": [],
            "future_plans_and_calls": "Not disclosed"
        }

    corpus, top = extract_top_corpus(docs)
    insight = call_llm(company, corpus)

    return {
        "company": company,
        "source": url,
        "concall_available": True,
        "documents_used": [{"url": d["url"], "type": d["type"], "len": d["len"]} for d in docs],
        "future_plans_and_calls": insight
    }


# ============================== CLI MODE ===========================

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python screener_future_plans.py <SCREENER_URL>")
        sys.exit(1)
    url = sys.argv[1]
    res = get_future_plans_from_screener(url)
    print(json.dumps(res, indent=2))
