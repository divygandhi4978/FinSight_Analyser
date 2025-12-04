import os
import re
import json
import time
import argparse
import logging
from urllib.parse import urljoin, urlparse, quote_plus
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from textwrap import wrap

import requests
from bs4 import BeautifulSoup

import pdfplumber
import docx

# --- LLM + RAG ---
from dotenv import load_dotenv
from groq import Groq  # direct Groq API client

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Optional: Selenium for JS-heavy pages
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service as ChromeService
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except Exception:
    SELENIUM_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

HEADERS = {
    "User-Agent": "FinSightScraper/1.0 (+https://example.com)"
}

# =============================================================================
# HTTP helpers
# =============================================================================

def http_get(url, session=None, timeout=20, max_retries=3, sleep=1):
    s = session or requests
    for attempt in range(1, max_retries + 1):
        try:
            r = s.get(url, headers=HEADERS, timeout=timeout)
            r.raise_for_status()
            return r
        except Exception as e:
            logging.warning(f"GET {url} failed (attempt {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(sleep * attempt)
    raise RuntimeError(f"Failed to GET {url} after {max_retries} attempts")


def get_page_html(url, use_selenium=False, wait=2):
    if use_selenium:
        if not SELENIUM_AVAILABLE:
            raise RuntimeError("Selenium requested but not available. Install selenium and webdriver-manager.")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        try:
            driver.get(url)
            time.sleep(wait)
            return driver.page_source
        finally:
            driver.quit()
    else:
        r = http_get(url)
        return r.text

# =============================================================================
# Screener resolution: company name / code / direct url
# =============================================================================

def resolve_screener_url(company_name=None, code=None, url=None, session=None):
    """
    Priority:
    - url (direct)
    - code (like NTPCGREEN)
    - company_name (search on Screener)
    """
    if url:
        full = url
        if not full.startswith("http"):
            raise ValueError("If you pass --url it must be a full URL starting with http")
        if not full.endswith('/'):
            full += '/'
        if 'consolidated' not in full:
            full = full.rstrip('/') + '/consolidated/'
        logging.info(f"Using direct URL: {full}")
        return full, url

    if code:
        base = f"https://www.screener.in/company/{code}/"
        if not base.endswith('/'):
            base += '/'
        full = base.rstrip('/') + '/consolidated/'
        logging.info(f"Using code '{code}' -> {full}")
        return full, code

    if not company_name:
        raise ValueError("One of --company, --code, or --url must be provided")

    base_search = "https://www.screener.in/search/?q="
    query = quote_plus(company_name)
    search_url = base_search + query
    logging.info(f"Searching Screener for company: {company_name} -> {search_url}")

    r = http_get(search_url, session=session)
    soup = BeautifulSoup(r.text, 'html.parser')

    candidate = None
    ul = soup.find('ul', class_=re.compile("search-list"))
    if ul:
        a_tags = ul.find_all('a', href=True)
        if a_tags:
            candidate = a_tags[0]['href']
    else:
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith("/company/"):
                candidate = href
                break

    if not candidate:
        raise RuntimeError(f"Could not find Screener company link for '{company_name}'")

    full_url = urljoin("https://www.screener.in", candidate)
    if not full_url.endswith('/'):
        full_url += '/'
    if 'consolidated' not in full_url:
        full_url = full_url.rstrip('/') + '/consolidated/'

    logging.info(f"Resolved company '{company_name}' to Screener URL: {full_url}")
    return full_url, company_name

# =============================================================================
# Link discovery & classification
# =============================================================================

def classify_link(href_lower, text_lower):
    annual_keywords = [
        'annual report', 'annual-report', 'ar20', 'annual_report'
    ]
    pres_keywords = [
        'presentation', 'investor presentation', 'investor-presentation',
        'deck', 'earnings presentation'
    ]
    concall_keywords = [
        'concall', 'conference call', 'earnings call', 'transcript',
        'earnings-transcript'
    ]

    combined = f"{href_lower} {text_lower}"

    if any(k in combined for k in annual_keywords):
        return 'annual'
    if any(k in combined for k in pres_keywords):
        return 'presentation'
    if any(k in combined for k in concall_keywords):
        return 'concall'
    return None


def find_documents_by_type(page_html, base_url, limit_each=5):
    soup = BeautifulSoup(page_html, 'html.parser')
    anchors = soup.find_all('a', href=True)

    annual_links = []
    pres_links = []
    concall_links = []
    seen = set()

    for a in anchors:
        href = a['href'].strip()
        text = (a.get_text() or '').strip()
        href_lower = href.lower()
        text_lower = text.lower()

        category = classify_link(href_lower, text_lower)
        if not category:
            continue

        full = urljoin(base_url, href)
        if full in seen:
            continue
        seen.add(full)

        row = {'url': full, 'text': text}

        if category == 'annual' and len(annual_links) < limit_each:
            annual_links.append(row)
        elif category == 'presentation' and len(pres_links) < limit_each:
            pres_links.append(row)
        elif category == 'concall' and len(concall_links) < limit_each:
            concall_links.append(row)

        if (
            len(annual_links) >= limit_each and
            len(pres_links) >= limit_each and
            len(concall_links) >= limit_each
        ):
            break

    logging.info(
        f"Classified links -> annual: {len(annual_links)}, "
        f"presentations: {len(pres_links)}, concall: {len(concall_links)}"
    )

    return {
        'annual_reports': annual_links,
        'presentations': pres_links,
        'concall_transcripts': concall_links
    }

# =============================================================================
# Download & text extraction
# =============================================================================

def download_file(url, out_folder, session=None, chunk_size=1024):
    os.makedirs(out_folder, exist_ok=True)
    local_name = os.path.basename(urlparse(url).path) or 'download'
    local_path = os.path.join(out_folder, local_name)
    base, ext = os.path.splitext(local_path)
    i = 1
    while os.path.exists(local_path):
        local_path = f"{base}_{i}{ext}"
        i += 1

    r = http_get(url, session=session)
    with open(local_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                f.write(chunk)
    return local_path


def extract_text_from_pdf(path):
    texts = []
    try:
        with pdfplumber.open(path) as pdf:
            for p in pdf.pages:
                texts.append(p.extract_text() or '')
        return '\n'.join(texts)
    except Exception as e:
        logging.warning(f"pdfplumber failed on {path}: {e}")
        return ''


def extract_text_from_docx(path):
    try:
        d = docx.Document(path)
        return '\n'.join(p.text for p in d.paragraphs)
    except Exception as e:
        logging.warning(f"docx extraction failed on {path}: {e}")
        return ''


def extract_text_from_html_content(html):
    soup = BeautifulSoup(html, 'html.parser')
    for s in soup(['script', 'style', 'noscript']):
        s.extract()
    return soup.get_text(separator=' ', strip=True)

# =============================================================================
# Financial + business extraction (heuristic)
# =============================================================================

def parse_number_from_line(line):
    is_negative = False
    if '(' in line and ')' in line:
        is_negative = True

    m = re.search(r'[-+]?\(?\s*[\d,]+(?:\.\d+)?\s*\)?', line)
    if not m:
        return None

    token = m.group(0)
    token = token.replace('(', '').replace(')', '').replace(',', '').strip()
    try:
        val = float(token)
    except ValueError:
        return None

    if is_negative and val > 0:
        val = -val
    return val


def detect_fiscal_year(text):
    m = re.search(r'year\s+ended[^0-9]{0,20}(20\d{2})', text, flags=re.IGNORECASE)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass

    m = re.search(r'(20\d{2})\s*[-–/]\s*(\d{2})', text)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass

    return None


def extract_business_info(text):
    business_description = None
    registered_office = None

    m = re.search(
        r'is\s+engaged\s+in\s+the\s+business\s+of\s+(.+?)[\.\n]',
        text, flags=re.IGNORECASE
    )
    if not m:
        m = re.search(
            r'company\s+is\s+a\s+leading\s+(.+?)[\.\n]',
            text, flags=re.IGNORECASE
        )
    if m:
        business_description = m.group(1).strip()

    lines = text.splitlines()
    for i, line in enumerate(lines):
        if 'registered office' in line.lower():
            block = [line.strip()]
            for j in range(i + 1, min(i + 6, len(lines))):
                if lines[j].strip():
                    block.append(lines[j].strip())
            registered_office = ' '.join(block)
            break

    return {
        'business_description': business_description,
        'registered_office': registered_office
    }


def extract_financial_figures(text):
    metrics = {
        'revenue': None,
        'ebitda': None,
        'ebit': None,
        'net_profit': None,
        'total_assets': None,
        'net_worth': None,
        'cfo': None,
        'cfi': None,
        'cff': None
    }

    metric_keywords = {
        'revenue': [
            'revenue from operations', 'total revenue', 'total income'
        ],
        'ebitda': [
            'ebitda', 'earnings before interest, tax, depreciation'
        ],
        'ebit': [
            'ebit', 'earnings before interest and tax', 'operating profit'
        ],
        'net_profit': [
            'profit for the year', 'profit after tax', 'pat', 'net profit'
        ],
        'total_assets': [
            'total assets'
        ],
        'net_worth': [
            "total equity", "net worth", "shareholders' funds", "shareholders’ funds"
        ],
        'cfo': [
            'cash flow from operating activities', 'net cash from operating activities'
        ],
        'cfi': [
            'cash flow from investing activities', 'net cash used in investing activities'
        ],
        'cff': [
            'cash flow from financing activities', 'net cash from financing activities'
        ]
    }

    lines = text.splitlines()
    for line in lines:
        lower = line.lower()
        if not any(c.isdigit() for c in line):
            continue

        for metric, kws in metric_keywords.items():
            if metrics[metric] is not None:
                continue
            if any(k in lower for k in kws):
                val = parse_number_from_line(line)
                if val is not None:
                    metrics[metric] = val

    return metrics

# =============================================================================
# Persist structured data
# =============================================================================

def save_structured_document(file_path, text, out_folder, meta):
    """
    Extract:
    - fiscal_year
    - financial metrics
    - business info (description, registered office)
    and save structured JSON.

    Also store the FULL raw text for RAG (no truncation in JSON).
    """
    os.makedirs(out_folder, exist_ok=True)

    fiscal_year = detect_fiscal_year(text)
    financials = extract_financial_figures(text)
    business_info = extract_business_info(text)

    file_basename = os.path.basename(file_path) if file_path else 'source'
    out_file = os.path.join(out_folder, file_basename + '.structured.json')

    # Also save a .txt with the full extracted text
    if text:
        txt_path = os.path.join(out_folder, file_basename + '.txt')
        with open(txt_path, 'w', encoding='utf-8') as tf:
            tf.write(text)
    else:
        txt_path = None

    result = {
        'file': os.path.abspath(file_path) if file_path else None,
        'meta': meta,
        'fiscal_year': fiscal_year,
        'financials': financials,
        'business_info': business_info,
        # FULL raw text – no truncation in stored JSON
        'raw_text_excerpt': text if text else "",
        'raw_text_txt_file': txt_path
    }

    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result

# =============================================================================
# Core pipeline
# =============================================================================

def process_target(company_name=None, code=None, url=None,
                   out_folder='out_documents', use_selenium=False,
                   delay=1.0):
    session = requests.Session()

    # 1. Resolve Screener URL
    screener_url, label = resolve_screener_url(
        company_name=company_name,
        code=code,
        url=url,
        session=session
    )

    # 2. Fetch HTML
    page_html = get_page_html(screener_url, use_selenium=use_selenium)

    # 3. Find categorized documents (annual / presentation / concall)
    docs_by_type = find_documents_by_type(page_html, screener_url, limit_each=5)

    structured_docs = []

    # 4. Iterate each category and download + extract + structure
    for category, links in docs_by_type.items():
        for item in links:
            link_url = item['url']
            link_text = item.get('text') or ''
            logging.info(f"Processing {category} doc: {link_url}")

            try:
                local = download_file(link_url, out_folder, session=session)
            except Exception as e:
                logging.warning(f"Failed to download {link_url}: {e}")
                continue

            ext = os.path.splitext(local)[1].lower()
            text = ''
            if ext == '.pdf':
                text = extract_text_from_pdf(local)
            elif ext in ('.docx', '.doc'):
                text = extract_text_from_docx(local)
            else:
                try:
                    r = http_get(link_url, session=session)
                    text = extract_text_from_html_content(r.text)
                except Exception as e:
                    logging.warning(f"Failed HTML extraction for {link_url}: {e}")
                    text = ''

            meta = {
                'source': link_url,
                'downloaded': local,
                'label': label,
                'category': category,   # annual/presentation/concall
                'link_text': link_text
            }
            structured = save_structured_document(local, text, out_folder, meta)
            structured_docs.append(structured)

            time.sleep(delay)

    # 5. Build company-level summary
    company_summary = {
        'label': label,
        'screener_url': screener_url,
        'documents': structured_docs
    }

    summary_path = os.path.join(out_folder, 'summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(company_summary, f, indent=2, ensure_ascii=False)
    logging.info(f"Saved company summary to {summary_path}")

    # 6. Cleanup: keep JSON + PDF + TXT, delete other junk
    cleanup_unwanted_files(out_folder)
    logging.info(f"Cleanup complete. Kept JSON, PDF and TXT in {out_folder}")

    return company_summary, structured_docs

# =============================================================================
# Cleanup
# =============================================================================

def cleanup_unwanted_files(out_folder):
    """
    Keep JSON + PDF + TXT.
    Delete other temp files (if any).
    """
    for root, dirs, files in os.walk(out_folder):
        for fname in files:
            lower = fname.lower()
            if lower.endswith('.json') or lower.endswith('.pdf') or lower.endswith('.txt'):
                continue
            try:
                full_path = os.path.join(root, fname)
                os.remove(full_path)
                logging.info(f"Deleted temporary file: {full_path}")
            except Exception as e:
                logging.warning(f"Failed to delete {full_path}: {e}")

# =============================================================================
# Simple TF-IDF Retriever (for RAG)
# =============================================================================

class TFIDFRetriever:
    """
    Very simple retriever over a list of documents.
    Each document is a dict with:
        - 'id'
        - 'content'
        - optional 'meta'
    """
    def __init__(self, docs):
        self.docs = docs
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words='english',
            max_features=20000
        )
        self.doc_texts = [d['content'] for d in docs]
        if not self.doc_texts:
            self.matrix = None
        else:
            self.matrix = self.vectorizer.fit_transform(self.doc_texts)

    def retrieve(self, query, top_k=3):
        if self.matrix is None or not self.doc_texts:
            return []
        q_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self.matrix)[0]
        idxs = sims.argsort()[::-1][:top_k]
        results = []
        for idx in idxs:
            d = self.docs[idx]
            results.append({
                'content': d['content'],
                'score': float(sims[idx]),
                'meta': d.get('meta', {})
            })
        return results

# =============================================================================
# Groq client initialisation + simple RAG wrapper
# =============================================================================

def init_groq_client():
    load_dotenv()
    # groq_api_key = os.getenv("GROQ_API_KEY")
    groq_api_key = "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"

    if not groq_api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment. Export it before running.")
    client = Groq(api_key=groq_api_key)
    return client


def rag_simple(query, retriever, client, top_k=3):
    """
    Basic RAG:
    - Retrieve top_k docs
    - Build truncated context
    - Call Groq chat.completions.create directly
    """
    results = retriever.retrieve(query, top_k=top_k)
    context = "\n\n".join([doc['content'] for doc in results]) if results else ""
    if not context:
        return "No relevant context found to answer the question."

    # HARD LIMIT on context length to avoid 400 errors from Groq
    MAX_CONTEXT_CHARS = 12000
    if len(context) > MAX_CONTEXT_CHARS:
        context = context[:MAX_CONTEXT_CHARS]

    prompt = f"""Use the following context to answer the question precisely and concisely. 
If the numbers in the context conflict, state the conflict instead of guessing.

Context:
{context}

Question: {query}

Answer in 2–6 sentences. If you mention any numbers (revenue, cash flow, profit etc.), clearly specify the year and units if available.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=512,
        temperature=0.1,
    )

    # Groq response structure is OpenAI-like
    if not response.choices:
        return "No answer returned from LLM."
    return response.choices[0].message.content.strip()

# =============================================================================
# Build retriever from structured_docs
# =============================================================================

def build_retriever_from_structured_docs(structured_docs):
    """
    Turn each structured doc into a text blob for retrieval.
    We combine:
    - business description
    - registered office
    - financials as text
    - raw_text_excerpt (TRUNCATED for RAG; full text stays in JSON/TXT)
    """
    docs_for_retriever = []
    MAX_RAW_PER_DOC = 8000  # chars per doc for retrieval

    for i, doc in enumerate(structured_docs):
        meta = doc.get('meta', {})
        label = meta.get('label') or ''
        category = meta.get('category') or ''
        fiscal_year = doc.get('fiscal_year')
        business_info = doc.get('business_info') or {}
        financials = doc.get('financials') or {}
        raw_text_full = doc.get('raw_text_excerpt') or ''

        # Truncate for retrieval but keep full in JSON/TXT
        raw_text_excerpt = raw_text_full[:MAX_RAW_PER_DOC]

        business_desc = business_info.get('business_description') or ''
        registered_office = business_info.get('registered_office') or ''

        financial_text_parts = []
        for k, v in financials.items():
            if v is None:
                continue
            financial_text_parts.append(f"{k}: {v}")

        financial_text = "\n".join(financial_text_parts)

        header = f"Document category: {category}. Label: {label}. Fiscal year: {fiscal_year}."
        meta_block = f"""
{header}

Business description:
{business_desc}

Registered office:
{registered_office}

Key financial metrics (as parsed):
{financial_text}
"""

        combined_content = meta_block + "\n\nRaw text excerpt:\n" + raw_text_excerpt

        docs_for_retriever.append({
            'id': f"doc_{i}",
            'content': combined_content,
            'meta': meta
        })

    return TFIDFRetriever(docs_for_retriever)

# =============================================================================
# CLI
# =============================================================================

def parse_args():
    parser = argparse.ArgumentParser(
        description='Company document scraper, numeric extractor, and LLM-powered QA (Screener.in)'
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--company', help='Company name (e.g. "Mindspace Business Parks REIT")')
    group.add_argument('--code', help='Screener company code (e.g. "NTPC")')
    group.add_argument('--url', help='Direct Screener URL (e.g. https://www.screener.in/company/NTPC/consolidated/)')
    parser.add_argument('--out', default='out_documents', help='Output folder')
    parser.add_argument('--selenium', action='store_true', help='Use Selenium to render JS-heavy pages')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between downloads (seconds)')

    # LLM / RAG specific
    parser.add_argument('--ask', help='Optional: question to ask the LLM over scraped docs')
    parser.add_argument('--top_k', type=int, default=3, help='Top K documents for RAG retrieval')

    return parser.parse_args()

# =============================================================================
# Save LLM answer to PDF
# =============================================================================

def save_answer_to_pdf(answer_text, out_folder, question=None):
    """
    Save the LLM answer (and optional question) as a simple PDF file.
    Returns the PDF path.
    """
    os.makedirs(out_folder, exist_ok=True)
    filename = f"llm_answer_{int(time.time())}.pdf"
    pdf_path = os.path.join(out_folder, filename)

    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4

    y = height - 50
    left_margin = 40
    line_height = 14
    max_chars_per_line = 90

    lines = []

    if question:
        lines.append(f"Question: {question}")
        lines.append("")
        lines.append("Answer:")
        lines.append("")

    for line in answer_text.splitlines():
        if not line.strip():
            lines.append("")
            continue
        for wrapped_line in wrap(line, max_chars_per_line):
            lines.append(wrapped_line)

    for line in lines:
        if y < 50:  # new page
            c.showPage()
            y = height - 50
        c.drawString(left_margin, y, line)
        y -= line_height

    c.save()
    logging.info(f"Saved LLM answer PDF to {pdf_path}")
    return pdf_path

# =============================================================================
# main
# =============================================================================

def main():
    args = parse_args()

    # 1) Scrape + extract + structure
    company_summary, structured_docs = process_target(
        company_name=args.company,
        code=args.code,
        url=args.url,
        out_folder=args.out,
        use_selenium=args.selenium,
        delay=args.delay
    )

    # 2) If user provided a question, run simple RAG with Groq LLM
    if args.ask:
        logging.info("Initialising Groq client and building retriever for QA...")
        client = init_groq_client()
        retriever = build_retriever_from_structured_docs(structured_docs)
        answer = rag_simple(args.ask, retriever, client, top_k=args.top_k)

        print("\n================ LLM ANSWER ================\n")
        print(answer)
        print("\n============================================\n")

        # Save answer as PDF
        pdf_path = save_answer_to_pdf(answer, args.out, question=args.ask)
        print(f"LLM answer saved to PDF: {pdf_path}")


if __name__ == '__main__':
    main()
