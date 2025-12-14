#!/usr/bin/env python3
"""
news_links.py

RESEARCH-GRADE COMPANY NEWS COLLECTOR

- Google News RSS
- Resolves REAL publisher URL (not news.google.com)
- Extracts article content (best-effort)
- Optional authoritative-domain filtering
- Safe for CLI and external imports
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse
import json
import sys
import time
import re

# ================= CONFIG =================

HEADERS = {
    "User-Agent": "PolicyLens-NewsResearch/1.0",
    "Accept-Language": "en-US,en;q=0.9"
}

AUTHORITATIVE_DOMAINS = [
    "moneycontrol.com",
    "livemint.com",
    "business-standard.com",
    "economictimes.indiatimes.com",
    "financialexpress.com",
    "cnbctv18.com",
    "reuters.com",
    "bloomberg.com"
]

MIN_CONTENT_LEN = 600

# ================= UTILITIES =================

def get_domain(url):
    try:
        return urlparse(url).netloc.lower()
    except:
        return ""

def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()

# ================= GOOGLE NEWS FIX =================

def extract_real_publisher_url(google_news_url):
    """
    Google News RSS links hide the real publisher.
    This function extracts the true article URL.
    """
    try:
        r = requests.get(google_news_url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, "lxml")

        # Google News article pages contain <a href="REAL_URL">
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("http") and "google.com" not in href:
                return href
    except:
        pass

    return google_news_url  # fallback

# ================= ARTICLE EXTRACTION =================

def extract_article_text(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        r.raise_for_status()
    except:
        return None

    if "text/html" not in r.headers.get("Content-Type", ""):
        return None

    soup = BeautifulSoup(r.text, "lxml")

    for tag in soup(["script", "style", "noscript", "header", "footer", "aside"]):
        tag.decompose()

    domain = get_domain(url)
    paragraphs = []

    # ---- DOMAIN-SPECIFIC PARSERS ----
    if "moneycontrol.com" in domain:
        block = soup.find("div", class_=re.compile("article_body|content_wrapper", re.I))
        if block:
            paragraphs = block.find_all("p")

    elif "livemint.com" in domain:
        block = soup.find("div", class_=re.compile("storyPage_content|content", re.I))
        if block:
            paragraphs = block.find_all("p")

    elif "economictimes.indiatimes.com" in domain:
        block = soup.find("div", class_=re.compile("articleBody|Normal", re.I))
        if block:
            paragraphs = block.find_all("p")

    # ---- FALLBACK ----
    if not paragraphs:
        paragraphs = soup.find_all("p")

    texts = [p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 60]
    content = clean_text(" ".join(texts))

    if len(content) < MIN_CONTENT_LEN:
        return None

    return content

# ================= CORE COLLECTOR =================

def collect_news(company, limit=10):
    rss_url = f"https://news.google.com/rss/search?q={quote_plus(company)}"
    r = requests.get(rss_url, headers=HEADERS, timeout=10)
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "xml")
    items = soup.find_all("item")

    results = []

    for item in items:
        if len(results) >= limit:
            break

        title = item.title.text.strip()
        gnews_link = item.link.text.strip()
        pub_date = item.pubDate.text.strip() if item.pubDate else None

        real_url = extract_real_publisher_url(gnews_link)
        domain = get_domain(real_url)

        content = extract_article_text(real_url)

        results.append({
            "title": title,
            "publisher_domain": domain,
            "published_at": pub_date,
            "url": real_url,
            "content_available": content is not None,
            "content": content
        })

    return results

# ================= PUBLIC API =================

def get_company_news(
    company: str,
    limit: int = 10,
    filter_authoritative: bool = False
):
    """
    External-callable API.
    Safe, structured, research-grade output.
    """

    raw_news = collect_news(company, limit=limit)

    if filter_authoritative:
        raw_news = [
            n for n in raw_news
            if any(dom in (n.get("publisher_domain") or "") for dom in AUTHORITATIVE_DOMAINS)
        ]

    return {
        "company": company,
        "collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit": limit,
        "authoritative_only": filter_authoritative,
        "news_count": len(raw_news),
        "news": raw_news
    }

# ================= CLI =================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python news_links.py <COMPANY_NAME>")
        sys.exit(1)

    company = sys.argv[1]
    result = get_company_news(company, limit=10, filter_authoritative=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))
