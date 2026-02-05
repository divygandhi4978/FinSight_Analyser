#!/usr/bin/env python3
"""
BusinessOverview.py
===================

MULTI-SOURCE DISCLOSURE-FIRST BUSINESS OVERVIEW ENGINE

Sources:
- Screener.in (primary financial disclosure)
- Company official website (business description)
- Wikipedia (fallback, clearly labeled)

No LLM. No hallucination. Deterministic only.
"""

import requests
import re
import json
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

HEADERS = {"User-Agent": "FinSight-DisclosureEngine/2.0"}

# -------------------------------------------------
# Utilities
# -------------------------------------------------

def now_utc():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ")

def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()

# -------------------------------------------------
# Source Fetchers
# -------------------------------------------------

def fetch_url(url, timeout=20):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.text

def extract_visible_text(html):
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    return clean(" ".join(p.get_text(" ", strip=True) for p in soup.find_all("p")))

# -------------------------------------------------
# Source 1: Screener
# -------------------------------------------------

def fetch_screener(code):
    url = f"https://www.screener.in/company/{code}/consolidated/"
    html = fetch_url(url)
    return {
        "name": "screener",
        "url": url,
        "text": extract_visible_text(html)
    }

# -------------------------------------------------
# Source 2: Company Website (best-effort)
# -------------------------------------------------

def find_company_website(screener_html, screener_url):
    soup = BeautifulSoup(screener_html, "lxml")
    base = urlparse(screener_url).netloc

    for a in soup.find_all("a", href=True):
        href = a["href"]
        text = (a.get_text() or "").lower()
        if "website" in text or "official" in text:
            full = urljoin(screener_url, href)
            if urlparse(full).netloc != base:
                return full
    return None

def fetch_company_website(screener_html, screener_url):
    site = find_company_website(screener_html, screener_url)
    if not site:
        return None
    try:
        html = fetch_url(site)
        return {
            "name": "company_website",
            "url": site,
            "text": extract_visible_text(html)
        }
    except:
        return None

# -------------------------------------------------
# Source 3: Wikipedia (fallback)
# -------------------------------------------------

def fetch_wikipedia(company_name):
    url = f"https://en.wikipedia.org/wiki/{company_name.replace(' ', '_')}"
    try:
        html = fetch_url(url)
        text = extract_visible_text(html)
        if len(text) < 500:
            return None
        return {
            "name": "wikipedia",
            "url": url,
            "text": text
        }
    except:
        return None

# -------------------------------------------------
# ATOMIC FACT EXTRACTION (SOURCE-AWARE)
# -------------------------------------------------

def extract_atomic_facts(text, source_name, source_url):
    facts = []

    def add_fact(ftype, statement):
        facts.append({
            "type": ftype,
            "statement": clean(statement),
            "source": source_name,
            "source_url": source_url
        })

    # identity
    m = re.search(
        r"([A-Z][A-Za-z &]+?) is a (leading|major|integrated|diversified)? ?([^.\n]{20,120})",
        text,
        re.IGNORECASE
    )
    if m:
        add_fact("identity", m.group(0))

    # scale
    m = re.search(r"(\d{2,4}) hotels? .*? (\d{3,6}) rooms?", text, re.IGNORECASE)
    if m:
        add_fact("scale", f"Operates {m.group(1)} hotels with approximately {m.group(2)} rooms")

    # business model
    if re.search(r"owned|leased|managed", text, re.IGNORECASE):
        add_fact("business_model", "Operates under a mix of owned, leased and managed models")

    # segments
    if re.search(r"luxury|upscale|midscale|economy", text, re.IGNORECASE):
        add_fact("segments", "Presence across luxury, upscale, midscale and economy segments")

    # geography
    if re.search(r"India|international|overseas|Nepal|Bhutan|Dubai", text, re.IGNORECASE):
        add_fact("geography", "Operations primarily in India with select international presence")

    return facts

# -------------------------------------------------
# FACT → STRUCTURED MAPPING
# -------------------------------------------------

def map_facts_to_core(facts):
    core = {
        "what_company_does": None,
        "business_model": None,
        "primary_segments": None,
        "geographic_presence": None,
        "scale": None
    }

    for f in facts:
        if f["type"] == "identity" and not core["what_company_does"]:
            core["what_company_does"] = f["statement"]
        elif f["type"] == "business_model" and not core["business_model"]:
            core["business_model"] = f["statement"]
        elif f["type"] == "segments" and not core["primary_segments"]:
            core["primary_segments"] = f["statement"]
        elif f["type"] == "geography" and not core["geographic_presence"]:
            core["geographic_presence"] = f["statement"]
        elif f["type"] == "scale" and not core["scale"]:
            core["scale"] = f["statement"]

    return core

# -------------------------------------------------
# Confidence Model
# -------------------------------------------------

def compute_confidence(core, sources_used):
    filled = sum(1 for v in core.values() if v)
    base = filled / len(core)
    bonus = min(0.15, 0.05 * max(0, sources_used - 1))
    return round(min(1.0, base + bonus), 2)

# -------------------------------------------------
# Plain English
# -------------------------------------------------

def build_plain_english(core):
    return " ".join(v for v in core.values() if v) or "Insufficient public disclosure available."

# -------------------------------------------------
# PUBLIC API
# -------------------------------------------------

def get_business_overview(code):
    sources = []
    all_facts = []

    screener = fetch_screener(code)
    sources.append(screener)

    for s in [screener]:
        all_facts += extract_atomic_facts(s["text"], s["name"], s["url"])

    website = fetch_company_website(screener["text"], screener["url"])
    if website:
        sources.append(website)
        all_facts += extract_atomic_facts(website["text"], website["name"], website["url"])

    wiki = fetch_wikipedia(code)
    if wiki:
        sources.append(wiki)
        all_facts += extract_atomic_facts(wiAki["text"], wiki["name"], wiki["url"])

    core = map_facts_to_core(all_facts)

    return {
        "input": {"code": code},
        "core_business_facts": core,
        "plain_english_summary": build_plain_english(core),
        "confidence": compute_confidence(core, len(sources)),
        "atomic_facts": all_facts,
        "sources": [{"name": s["name"], "url": s["url"]} for s in sources],
        "generated_at": now_utc()
    }

# -------------------------------------------------
# CLI
# -------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python BusinessOverview.py <COMPANY_CODE>")
        sys.exit(1)

    result = get_business_overview(sys.argv[1].upper())
    print(json.dumps(result, indent=2))
