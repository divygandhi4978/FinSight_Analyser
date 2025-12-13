#!/usr/bin/env python3
"""
collect_company_news_with_content.py

BASIC RESEARCH-GRADE NEWS COLLECTOR

- Google News RSS
- Resolves publisher URL
- Extracts published article content
- Graceful fallback if blocked
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse
import json
import sys
import time
import re

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
    "cnbctv18.com"
]

# ------------------ helpers ------------------
def is_html_response(url):
    try:
        r = requests.head(url, headers=HEADERS, timeout=5, allow_redirects=True)
        return "text/html" in r.headers.get("Content-Type", "")
    except:
        return False


def normalize_url(url):
    if not url:
        return None
    # remove tracking params
    return url.split("?")[0]

def resolve_final_url(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        return r.url
    except:
        return url

def get_domain(url):
    try:
        return urlparse(url).netloc.lower()
    except:
        return ""

def clean_text(text):
    text = re.sub(r"\s+", " ", text)
    return text.strip()
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

    # -------- DOMAIN-SPECIFIC LOGIC --------
    if "moneycontrol.com" in domain:
        article = soup.find("div", class_=re.compile("article_body|content_wrapper", re.I))
        if article:
            paragraphs = article.find_all("p")

    elif "livemint.com" in domain:
        article = soup.find("div", class_=re.compile("storyPage_content|content", re.I))
        if article:
            paragraphs = article.find_all("p")

    elif "economictimes.indiatimes.com" in domain:
        article = soup.find("div", class_=re.compile("articleBody|Normal", re.I))
        if article:
            paragraphs = article.find_all("p")

    # -------- GENERIC FALLBACK --------
    if not paragraphs:
        paragraphs = soup.find_all("p")

    texts = []
    for p in paragraphs:
        t = p.get_text(strip=True)
        if len(t) > 60:
            texts.append(t)

    content = clean_text(" ".join(texts))

    # HARD QUALITY GATE
    if len(content) < 600:
        return None

    return content

# ------------------ main collector ------------------
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

        # 1️⃣ resolve redirect (fast timeout)
        try:
            final_url = requests.get(
                gnews_link,
                headers=HEADERS,
                timeout=5,
                allow_redirects=True
            ).url
        except:
            continue

        domain = get_domain(final_url)

        # 2️⃣ fetch article content (fast fail)
        content = None
        try:
            content = extract_article_text(final_url)
        except:
            pass

        results.append({
            "title": title,
            "publisher_domain": domain,
            "published_at": pub_date,
            "url": final_url,
            "content_available": content is not None,
            "content": content
        })

    return results


# ------------------ CLI ------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python collect_company_news_with_content.py <COMPANY_NAME>")
        sys.exit(1)

    company = sys.argv[1]
    news = collect_news(company)

    print(json.dumps({
        "company": company,
        "news_count": len(news),
        "news": news
    }, indent=2, ensure_ascii=False))
