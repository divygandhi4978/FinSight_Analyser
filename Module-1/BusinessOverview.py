#!/usr/bin/env python3
"""
Improved Lightweight Business Overview API

Changes vs original:
- Detects and includes the company's official website (if linked on Screener page).
- Finds and prioritizes Annual Report PDFs (searches link text for 'annual', 'annual report', or recent year patterns).
- Attempts to extract text from PDFs using pdfplumber (if installed); falls back to placeholder when not available.
- More robust HTML link discovery and filtering (avoids internal/same-domain noise).
- Slightly stronger 'simple' business info extractor (looks for 'is a' sentences and 'founded' patterns).
- Better logging and clearer returned doc metadata (source, link_text, content_length, is_pdf).

Usage unchanged from original script.
"""

import os
import re
import json
import time
import logging
from io import BytesIO
from urllib.parse import urljoin, urlparse, quote_plus
import requests
from bs4 import BeautifulSoup

# Optional dependency for PDF extraction
try:
    import pdfplumber
    _HAS_PDFPLUMBER = True
except Exception:
    pdfplumber = None
    _HAS_PDFPLUMBER = False

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
HEADERS = {"User-Agent": "FinSightDevKey/1.0"}

# ---------------------------
# DEV KEY: paste your key here for quick local dev
DEV_API_KEY = "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"

# ------------------ HTTP helpers ------------------
def http_get(url, timeout=20):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r


def extract_text_from_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    for s in soup(['script', 'style', 'noscript']):
        s.extract()
    # collapse whitespace
    return ' '.join(soup.get_text(separator=' ').split())

# ------------------ Screener resolution & doc discovery (improved) ------------------

def resolve_screener_url(company_name=None, code=None, url=None):
    """
    Build screener.in company URL heuristically.
    If code provided → use as-is. If company_name provided → convert to uppercase
    and remove non-alphanumeric characters. This produces a best-effort Screener URL.
    """
    if url:
        return url
    if code:
        final_code = re.sub(r'[^A-Za-z0-9]', '', code.upper())
        return f"https://www.screener.in/company/{final_code}/consolidated/"
    if company_name:
        final_code = re.sub(r'[^A-Za-z0-9]', '', company_name.upper())
        return f"https://www.screener.in/company/{final_code}/consolidated/"
    raise ValueError("Provide --company, --code, or --url")


def _is_external_link(href, base_netloc):
    try:
        parsed = urlparse(href)
        if not parsed.netloc:
            return False
        return parsed.netloc and parsed.netloc != base_netloc
    except Exception:
        return False


def find_document_links(screener_html, base_url, limit=8):
    """
    Discover candidate resources from the Screener company page.
    - Prefer PDFs (annual reports, presentations).
    - Capture external official website if present.
    - Return up to `limit` ordered by likely relevance.
    """
    soup = BeautifulSoup(screener_html, 'html.parser')
    anchors = soup.find_all('a', href=True)
    base_netloc = urlparse(base_url).netloc
    pdfs = []
    externals = []
    general = []

    for a in anchors:
        href = a['href'].strip()
        if not href:
            continue
        full = urljoin(base_url, href)
        text = (a.get_text() or '').strip()
        low_text = text.lower()
        lower_href = href.lower()

        # Skip anchors that link back to the same page fragment
        if lower_href.startswith('#'):
            continue

        # Candidate annual report / pdf
        if '.pdf' in lower_href or 'annual' in low_text or 'report' in low_text or 'presentation' in low_text:
            pdfs.append({'url': full, 'text': text or lower_href, 'is_pdf': '.pdf' in lower_href})
            continue

        # external official website heuristics
        if _is_external_link(full, base_netloc):
            # textual hints
            if 'website' in low_text or 'official' in low_text or 'visit' in low_text or 'www.' in lower_href:
                externals.insert(0, {'url': full, 'text': text or full, 'is_pdf': False})
                continue
            # sometimes the company site is present with domain in href - treat as external candidate
            parsed = urlparse(full)
            if parsed.netloc and parsed.netloc != base_netloc:
                general.append({'url': full, 'text': text or full, 'is_pdf': False})

    # Compose result: prefer explicit externals, then PDFs, then general externals
    out = []
    for x in externals:
        if x not in out:
            out.append(x)
        if len(out) >= limit:
            return out
    for x in pdfs:
        if x not in out:
            out.append(x)
        if len(out) >= limit:
            return out
    for x in general:
        if x not in out:
            out.append(x)
        if len(out) >= limit:
            return out
    return out

# ------------------ Download + extract (improved) ------------------

def download_text_from_url(url):
    """
    Fetch URL and extract text. If PDF, attempt to use pdfplumber to read and extract plain text.
    Returns extracted text (possibly short) or an empty string on failure.
    """
    try:
        r = http_get(url)
        ctype = r.headers.get('content-type', '')
        # PDF handling
        if 'pdf' in ctype or url.lower().endswith('.pdf'):
            if _HAS_PDFPLUMBER:
                try:
                    with pdfplumber.open(BytesIO(r.content)) as pdf:
                        pages = []
                        for p in pdf.pages:
                            txt = p.extract_text()
                            if txt:
                                pages.append(txt)
                        full = '\n'.join(pages)
                        return full if full.strip() else f"[PDF (empty text) from {url}]"
                except Exception as e:
                    logging.warning(f"pdfplumber failed for {url}: {e}")
                    return f"[PDF CONTENT FROM {url} — pdfplumber failed: {e}]"
            else:
                return f"[PDF CONTENT FROM {url} — pdfplumber not installed]"
        # HTML
        return extract_text_from_html(r.text)
    except Exception as e:
        logging.warning(f"Failed to fetch {url}: {e}")
        return ''

# ------------------ Simple structured extract (slightly stronger) ------------------

def simple_extract_business_info(text):
    if not text:
        return {
            'business_description': None,
            'registered_office': None,
            'founded': None,
        }
    # find first "is a/an/the" style sentence (short)
    m = re.search(r"([A-Z][^.\n]{10,250}?\b(is|was)\b\s+(a|an|the)\b[^.\n]{0,200}\.)", text, flags=re.IGNORECASE)
    descr = m.group(1).strip() if m else None

    # registered office
    m2 = re.search(r"registered office[:\-]?\s*([^\.\n]{10,200})", text, flags=re.IGNORECASE)
    reg = m2.group(1).strip() if m2 else None

    # founded / incorporated year
    m3 = re.search(r"founded\s+in\s+(\d{4})|incorporated\s+in\s+(\d{4})|established\s+in\s+(\d{4})", text, flags=re.IGNORECASE)
    founded = None
    if m3:
        for g in m3.groups():
            if g and g.isdigit():
                founded = g
                break

    return {'business_description': descr, 'registered_office': reg, 'founded': founded}

# ------------------ Retriever ------------------
class TFIDFRetriever:
    def __init__(self, docs):
        self.docs = docs
        texts = [d['content'] for d in docs]
        self.vectorizer = TfidfVectorizer(lowercase=True, stop_words='english', max_features=10000)
        self.matrix = self.vectorizer.fit_transform(texts) if texts else None

    def retrieve(self, query, top_k=3):
        if self.matrix is None:
            return []
        qvec = self.vectorizer.transform([query])
        sims = cosine_similarity(qvec, self.matrix)[0]
        idxs = sims.argsort()[::-1][:top_k]
        return [{'content': self.docs[i]['content'], 'meta': self.docs[i].get('meta', {}), 'score': float(sims[i])} for i in idxs]

# ------------------ LLM client init (env-based with DEV fallback) ------------------
def init_llm_client(provider='groq'):
    provider = provider.lower()
    if provider == 'groq':
        try:
            from groq import Groq
        except Exception as e:
            raise RuntimeError('Groq SDK not installed: ' + str(e))
        key = os.getenv('GROQ_API_KEY') or DEV_API_KEY
        if not key or key == "<PASTE_YOUR_API_KEY_HERE>":
            raise RuntimeError('GROQ_API_KEY not set in env and DEV_API_KEY not provided. Paste key into DEV_API_KEY.')
        return Groq(api_key=key)
    elif provider == 'openai':
        try:
            import openai
        except Exception as e:
            raise RuntimeError('openai package not installed: ' + str(e))
        key = os.getenv('OPENAI_API_KEY') or DEV_API_KEY
        if not key or key == "<PASTE_YOUR_API_KEY_HERE>":
            raise RuntimeError('OPENAI_API_KEY not set in env and DEV_API_KEY not provided. Paste key into DEV_API_KEY.')
        openai.api_key = key
        return openai
    else:
        raise ValueError('Unsupported provider: use groq or openai')

# ------------------ Overview generator (same as before) ------------------
REQUIRED_SECTIONS = ['Headline','Snapshot','Where they operate','What they do','Key customers/segments','Scale & distribution','Competitive position','Recent strategic moves & risks','Conclusion']

def build_prompt(company_name, retrieved_docs, word_limit=2000):
    ctx = []
    for i,d in enumerate(retrieved_docs):
        src = d.get('meta', {}).get('source') or d.get('meta', {}).get('downloaded') or f'DOC{i+1}'
        txt = d['content'][:4000] if d['content'] else ''
        ctx.append(f"--- SOURCE {i+1}: {src} ---\n" + txt)
    context = '\n\n'.join(ctx)
    prompt = f"""
Use ONLY the CONTEXT below to write a concise BUSINESS OVERVIEW for {company_name}.
Do NOT hallucinate. If a fact isn't in context, write (not found in sources).
Include EXACT headings: {', '.join(REQUIRED_SECTIONS)}.
Max {word_limit} words.
Context:
{context}

Write the overview:
"""
    return prompt


def call_llm(client, provider, prompt, max_tokens=800):
    provider = provider.lower()
    if provider == 'groq':
        resp = client.chat.completions.create(model='llama-3.1-8b-instant', messages=[{'role':'user','content':prompt}], max_tokens=max_tokens, temperature=0.0)
        return resp.choices[0].message.content.strip()
    elif provider == 'openai':
        resp = client.ChatCompletion.create(model='gpt-4o-mini', messages=[{'role':'user','content':prompt}], max_tokens=max_tokens, temperature=0.0)
        return resp.choices[0].message['content'].strip()
    else:
        raise ValueError('unknown provider')


def generate_business_overview(company_name, retriever, client, provider='groq', top_k=3, word_limit=900):
    retrieved = retriever.retrieve(company_name + ' business overview', top_k=top_k)
    if not retrieved:
        return {'error':'no_docs'}
    prompt = build_prompt(company_name, retrieved, word_limit=word_limit)
    text = call_llm(client, provider, prompt)
    wc = len(text.split())
    missing = [h for h in REQUIRED_SECTIONS if h not in text]
    return {'overview': text, 'word_count': wc, 'missing_headings': missing, 'sources': [d.get('meta',{}).get('source') for d in retrieved]}

# ------------------ Small direct API entry-points (improved) ------------------

def scrape_and_extract(company=None, code=None, url=None, limit_links=6):
    screener = resolve_screener_url(company_name=company, code=code, url=url)
    logging.info(f'Resolved screener URL: {screener}')
    r = http_get(screener)

    links = find_document_links(r.text, screener, limit=limit_links)
    logging.info(f'Found {len(links)} candidate links on screener page')

    docs = []

    # Add main screener page as a doc
    main_text = extract_text_from_html(r.text)
    docs.append({'content': main_text, 'meta': {'source': screener}, 'business_info': simple_extract_business_info(main_text)})

    # Download candidate links; prioritize PDF annual report if any
    # Heuristic: prefer links whose text contains 'annual' or looks like a year
    pdf_candidates = []
    other_candidates = []
    for link in links:
        text = link.get('text','') or ''
        low = text.lower()
        if 'annual' in low or re.search(r'\b20\d{2}\b', text):
            pdf_candidates.append(link)
        else:
            other_candidates.append(link)

    ordered = pdf_candidates + other_candidates

    for link in ordered:
        txt = download_text_from_url(link['url'])
        meta = {'source': link['url'], 'link_text': link.get('text'), 'is_pdf': link.get('is_pdf', False), 'content_length': len(txt or '')}
        biz = simple_extract_business_info(txt)
        docs.append({'content': txt, 'meta': meta, 'business_info': biz})

    return docs


def build_retriever_from_texts(structured_docs):
    docs_for = [{'content': d['content'], 'meta': d.get('meta',{})} for d in structured_docs]
    return TFIDFRetriever(docs_for)

# ------------------ CLI ------------------

def parse_args():
    import argparse
    p = argparse.ArgumentParser()
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument('--company')
    grp.add_argument('--code')
    grp.add_argument('--url')
    p.add_argument('--provider', choices=['groq','openai'], default='groq')
    p.add_argument('--overview', action='store_true')
    p.add_argument('--top_k', type=int, default=3)
    return p.parse_args()


def main():
    args = parse_args()
    docs = scrape_and_extract(company=args.company, code=args.code, url=args.url)
    retriever = build_retriever_from_texts(docs)
    if args.overview:
        client = init_llm_client(provider=args.provider)
        result = generate_business_overview(args.company or args.code or args.url, retriever, client, provider=args.provider, top_k=args.top_k)
        print('Word count:', result.get('word_count'))
        print('Missing headings:', result.get('missing_headings'))
        print('\n--- Overview preview ---\n')
        print(result.get('overview')[:4000])

if __name__ == '__main__':
    main()
