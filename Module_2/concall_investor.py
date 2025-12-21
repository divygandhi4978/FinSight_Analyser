#!/usr/bin/env python3
"""
screener_concall_investor_future_plans_rag.py

SOURCE OF TRUTH:
- Screener.in company page

PIPELINE:
Screener →
  → Latest 3 Concall Transcripts
  → Latest 3 Investor Presentations
→ Text Extraction (PDF / HTML)
→ RAG (TF-IDF)
→ LLM (grounded)
→ Important Calls + Future Business Plans

No news. No guessing. Primary disclosures only.
"""

import requests
import re
import sys
from io import BytesIO
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# ---------------- PDF ----------------
try:
    import pdfplumber
    HAS_PDF = True
except:
    HAS_PDF = False

# ---------------- RAG ----------------
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# ---------------- LLM ----------------
from groq import Groq

# ================= CONFIG =================

HEADERS = {
    "User-Agent": "PolicyLens-ScreenerRAG/1.1"
}

MIN_TEXT_LEN = 800
MAX_CONCALLS = 3
MAX_PRESENTATIONS = 3

FUTURE_QUERIES = [
    "future plans",
    "expansion",
    "capital expenditure",
    "capex",
    "pipeline",
    "growth strategy",
    "guidance",
    "outlook",
    "next year",
    "next two years",
    "FY26",
    "FY27"
]

# ================= HELPERS =================

def fetch_html(url):
    r = requests.get(url, headers=HEADERS, timeout=25)
    r.raise_for_status()
    return r.text


def extract_pdf_text(url):
    if not HAS_PDF:
        return None
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        with pdfplumber.open(BytesIO(r.content)) as pdf:
            text = "\n".join(p.extract_text() or "" for p in pdf.pages)
        return text if len(text) > MIN_TEXT_LEN else None
    except:
        return None


def extract_html_text(html):
    soup = BeautifulSoup(html, "lxml")
    for t in soup(["script", "style", "noscript", "header", "footer"]):
        t.decompose()
    text = " ".join(p.get_text(" ", strip=True) for p in soup.find_all("p"))
    return text if len(text) > MIN_TEXT_LEN else None


def extract_date_from_text(text):
    """Best-effort date extraction"""
    m = re.search(r"(Q[1-4]\s*FY\d{2,4}|FY\d{2,4}|March|June|September|December)\s*\d{0,4}", text, re.I)
    return m.group(0) if m else "Date not explicitly mentioned"

# ================= SCREENER LINK FINDERS =================

def find_screener_links(screener_url, keywords, max_links):
    html = fetch_html(screener_url)
    soup = BeautifulSoup(html, "lxml")

    links = []

    for a in soup.find_all("a", href=True):
        text = (a.get_text() or "").lower()
        href = a["href"].lower()

        if any(k in text or k in href for k in keywords):
            full = urljoin(screener_url, a["href"])
            links.append(full)

    # de-duplicate while preserving order
    uniq = []
    for l in links:
        if l not in uniq:
            uniq.append(l)

    return uniq[:max_links]


def find_concall_links(screener_url):
    return find_screener_links(
        screener_url,
        keywords=["concall", "conference call", "earnings call", "transcript"],
        max_links=MAX_CONCALLS
    )


def find_investor_presentation_links(screener_url):
    return find_screener_links(
        screener_url,
        keywords=["investor presentation", "presentation"],
        max_links=MAX_PRESENTATIONS
    )

# ================= DOCUMENT LOADER =================

def load_docs(links, doc_type):
    docs = []

    for link in links:
        print(f"Fetching {doc_type}: {link}")

        if link.lower().endswith(".pdf"):
            text = extract_pdf_text(link)
        else:
            html = fetch_html(link)
            text = extract_html_text(html)

        if not text:
            continue

        docs.append({
            "content": text,
            "meta": {
                "type": doc_type,
                "source": link,
                "date_hint": extract_date_from_text(text)
            }
        })

    return docs

# ================= RAG =================

class TFIDFRetriever:
    def __init__(self, docs):
        self.docs = docs
        texts = [d["content"] for d in docs]
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=15000,
            ngram_range=(1, 2)
        )
        self.matrix = self.vectorizer.fit_transform(texts)

    def retrieve(self, query, top_k=3):
        qv = self.vectorizer.transform([query])
        sims = cosine_similarity(qv, self.matrix)[0]
        idxs = sims.argsort()[::-1][:top_k]
        return [self.docs[i] for i in idxs]

# ================= LLM =================
api1="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" #Krish
api2="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"
def call_llm(prompt):
    client = Groq(api_key=api2)
    r = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=1000
    )
    return r.choices[0].message.content.strip()

# ================= EXTRACTION =================
def extract_keyword_snippets(text, keywords, window=300, max_snippets=5):
    """
    Extracts small text snippets around keywords.
    Deterministic. No LLM.
    """
    snippets = []
    text_lower = text.lower()

    for kw in keywords:
        pos = text_lower.find(kw.lower())
        if pos == -1:
            continue

        start = max(0, pos - window)
        end = min(len(text), pos + window)
        snippet = text[start:end].strip()

        if snippet and snippet not in snippets:
            snippets.append(snippet)

        if len(snippets) >= max_snippets:
            break

    return snippets
def build_prompt(company, snippets):
    ctx = "\n\n".join(
        f"SOURCE TYPE: {s['meta']['type']}\n"
        f"SOURCE LINK: {s['meta']['source']}\n"
        f"DATE HINT: {s['meta']['date_hint']}\n"
        f"SNIPPET:\n{s['snippet']}"
        for s in snippets
    )

    return f"""
You are a senior equity research analyst.

Extract ONLY what is explicitly stated in the snippets.
Do NOT infer. Do NOT guess.

Output VALID JSON ONLY.

JSON SCHEMA:
{{
  "analysis": {{
    "important_management_calls": [],
    "future_business_plans": [],
    "expansion_pipeline": [],
    "capex_plans": {{
      "mentioned": false,
      "details": []
    }},
    "management_guidance": [],
    "key_risks_highlighted": [],
    "timeline_summary": []
  }},
  "plain_english_summary": {{
    "what_the_company_is_doing": "",
    "where_the_company_is_investing": "",
    "what_management_is_confident_about": "",
    "what_can_go_wrong": "",
    "big_picture_outlook": ""
  }}
}}

SNIPPETS:
{ctx}
"""


def extract_future_plans(company, retriever):
    keyword_snippets = []

    for q in FUTURE_QUERIES:
        docs = retriever.retrieve(q, top_k=1)

        for d in docs:
            snippets = extract_keyword_snippets(
                d["content"],
                keywords=[q],
                window=250,
                max_snippets=2
            )

            for s in snippets:
                keyword_snippets.append({
                    "snippet": s,
                    "meta": d["meta"]
                })

    # HARD STOP: no facts → no LLM
    if not keyword_snippets:
        return {
            "analysis": {},
            "plain_english_summary": {}
        }

    prompt = build_prompt(company, keyword_snippets)
    return call_llm(prompt)

# ================= MAIN =================

def main():
    if len(sys.argv) < 2:
        print("Usage: python screener_concall_investor_future_plans_rag.py <SCREENER_URL>")
        sys.exit(1)

    screener_url = sys.argv[1]
    company = screener_url.rstrip("/").split("/")[-2]

    print("🔍 Finding concall links on Screener...")
    concall_links = find_concall_links(screener_url)

    print("🔍 Finding investor presentation links on Screener...")
    presentation_links = find_investor_presentation_links(screener_url)

    if not concall_links and not presentation_links:
        print("❌ No concall or investor presentation links found.")
        return

    docs = []
    docs += load_docs(concall_links, "concall")
    docs += load_docs(presentation_links, "investor_presentation")

    if not docs:
        print("❌ Failed to extract text from all documents.")
        return

    retriever = TFIDFRetriever(docs)

    print("\n🧠 Extracting future business plans & important calls...\n")
    result = extract_future_plans(company, retriever)

    print("========== FINAL OUTPUT ==========\n")
    print(result)


#External Caller
def get_future_plans_from_screener(
    screener_url: str,
    max_concalls: int = MAX_CONCALLS,
    max_presentations: int = MAX_PRESENTATIONS
):
    """
    Public API for external callers.

    ALWAYS returns a stable schema.
    Concall / presentation availability is explicitly signaled.
    """

    company = screener_url.rstrip("/").split("/")[-2]

    concall_links = find_concall_links(screener_url)[:max_concalls]
    presentation_links = find_investor_presentation_links(screener_url)[:max_presentations]

    # Case 1: No documents at all
    if not concall_links and not presentation_links:
        return {
            "company": company,
            "source": screener_url,
            "concall_available": False,
            "documents_used": [],
            "future_plans_and_calls": "Not disclosed"
        }

    docs = []
    docs += load_docs(concall_links, "concall")
    docs += load_docs(presentation_links, "investor_presentation")

    # Case 2: Links found but text extraction failed
    if not docs:
        return {
            "company": company,
            "source": screener_url,
            "concall_available": False,
            "documents_used": [],
            "future_plans_and_calls": "Not disclosed"
        }

    retriever = TFIDFRetriever(docs)
    extracted_text = extract_future_plans(company, retriever)

    return {
        "company": company,
        "source": screener_url,
        "concall_available": True,
        "documents_used": [
            {
                "type": d["meta"]["type"],
                "source": d["meta"]["source"],
                "date_hint": d["meta"]["date_hint"]
            }
            for d in docs
        ],
        "future_plans_and_calls": extracted_text or "Not disclosed"
    }


if __name__ == "__main__":
    main()
