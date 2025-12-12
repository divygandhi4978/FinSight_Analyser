#!/usr/bin/env python3
"""
extract_screener_financials.py

Same extractor as you provided but:
- exposes `get_financials(code: str) -> dict`
- does NOT save to disk
- when run as __main__ prints JSON to stdout
"""
import sys
import json
import time
import requests
import pandas as pd
import numpy as np
from io import StringIO
from typing import Dict, Any, Optional, Tuple, List
from bs4 import BeautifulSoup

BASE = "https://www.screener.in/company/{code}/consolidated/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

SECTION_KEYWORDS = {
    "profit_and_loss": ["sales", "operating profit", "net profit", "other income", "depreciation", "profit before tax"],
    "balance_sheet": ["equity", "reserves", "borrowings", "total liabilities", "fixed assets", "investments", "total assets"],
    "cash_flows": ["cash from operating", "cash from investing", "cash from financing", "net cash flow"]
}

def clean_label(s: str) -> str:
    if s is None:
        return ""
    s = str(s).replace("\xa0", " ").replace("\u200b", "").strip()
    s = s.rstrip(":").strip()
    s = s.replace("+", "").strip()
    s = " ".join(s.split())
    return s

def to_number_cell(x):
    if pd.isna(x): return None
    s = str(x).strip()
    if s == "": return None
    if s.endswith('%'): return s
    if s in ['-', '—', 'nan', 'None']: return None
    s = s.replace(',', '')
    if s.startswith('(') and s.endswith(')'):
        s = '-' + s[1:-1]
    filtered = ''.join(ch for ch in s if (ch.isdigit() or ch in '.-'))
    if filtered in ['', '.', '-']: return None
    try:
        val = float(filtered)
        return int(val) if val.is_integer() else val
    except:
        return s

def score_table_for_section(df: pd.DataFrame, section: str) -> float:
    kws = SECTION_KEYWORDS.get(section, [])
    score = 0.0
    try:
        first_col = df.iloc[:, 0].astype(str).str.lower().astype(str)
    except Exception:
        first_col = pd.Series(dtype=str)
    for kw in kws:
        score += first_col.str.contains(kw).sum() * 2.0
    score += df.shape[1] * 0.1
    headers = " ".join(map(str, df.columns)).lower()
    for kw in kws:
        if kw in headers:
            score += 1.0
    return float(score)

def pick_best_table(html_snippet: str, section: str, page_html_full: Optional[str]=None) -> pd.DataFrame:
    candidates = []
    if html_snippet and "<table" in html_snippet.lower():
        try:
            dfs = pd.read_html(StringIO(html_snippet))
            for df in dfs:
                candidates.append(df)
        except Exception:
            candidates = []
    best = None
    best_score = -1.0
    for df in candidates:
        s = score_table_for_section(df, section)
        if s > best_score:
            best_score = s
            best = df
    if (best is None or best_score < 0.1) and page_html_full:
        try:
            all_dfs = pd.read_html(StringIO(page_html_full))
            for df in all_dfs:
                s = score_table_for_section(df, section)
                if s > best_score:
                    best_score = s
                    best = df
        except Exception:
            pass
    if best is None:
        raise ValueError(f"No table found for section '{section}'")
    best = best.rename(columns={best.columns[0]: 'line_item'}).set_index('line_item')
    best.index = [clean_label(i) for i in best.index]
    best.columns = [clean_label(c) for c in best.columns]
    return best

def df_to_json_like(df: pd.DataFrame) -> Dict[str, Any]:
    df_clean = df.apply(lambda col: col.map(to_number_cell))
    periods = [str(c) for c in df_clean.columns]
    data = {}
    for r in df_clean.index:
        rowdict = {}
        for p in df_clean.columns:
            v = df_clean.at[r, p]
            if isinstance(v, (np.integer,)):
                v = int(v)
            elif isinstance(v, (np.floating,)):
                if float(v).is_integer():
                    v = int(v)
                else:
                    v = float(v)
            rowdict[str(p)] = v
        data[str(r)] = rowdict
    return {"units": "Rs. Crores", "periods": periods, "data": data}

def find_section_html(page_html: str, section_anchor: str) -> Optional[str]:
    lower = page_html.lower()
    token = f'<section id="{section_anchor.lower()}"'
    pos = lower.find(token)
    if pos == -1:
        token2 = f'id="{section_anchor.lower()}"'
        pos = lower.find(token2)
        if pos == -1:
            return None
    start = page_html.rfind('<section', 0, pos)
    if start == -1:
        start = pos
    end = page_html.find('</section>', pos)
    if end == -1:
        end = len(page_html)
    else:
        end = end + len('</section>')
    return page_html[start:end]

def reconcile_cashflow_section(cf_json: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    diag = {"reconciliation": []}
    periods = cf_json.get("periods", [])
    data = cf_json.get("data", {})
    keymap = {"CFO": None, "CFI": None, "CFF": None, "NET_reported": None}
    for k in data.keys():
        low = k.lower()
        if "operat" in low and "cash" in low and keymap["CFO"] is None:
            keymap["CFO"] = k
        if "invest" in low and "cash" in low and keymap["CFI"] is None:
            keymap["CFI"] = k
        if "financ" in low and "cash" in low and keymap["CFF"] is None:
            keymap["CFF"] = k
        if ("net cash" in low or ("net" in low and "cash" in low)) and keymap["NET_reported"] is None:
            keymap["NET_reported"] = k
    if keymap["CFO"] is None:
        for cand in ["cash from operating activity","cash from operations","cash from operating"]:
            for k in data.keys():
                if cand in k.lower():
                    keymap["CFO"] = k; break
            if keymap["CFO"]: break
    if keymap["CFI"] is None:
        for cand in ["cash from investing activity","cash from investing"]:
            for k in data.keys():
                if cand in k.lower():
                    keymap["CFI"] = k; break
            if keymap["CFI"]: break
    if keymap["CFF"] is None:
        for cand in ["cash from financing activity","cash from financing"]:
            for k in data.keys():
                if cand in k.lower():
                    keymap["CFF"] = k; break
            if keymap["CFF"]: break

    canonical = {
        "units": cf_json.get("units", "Rs. Crores"),
        "periods": periods,
        "data": {
            "Cash from Operating Activity": {},
            "Cash from Investing Activity": {},
            "Cash from Financing Activity": {},
            "Net Cash Flow": {},
            "reported_net": {}
        }
    }

    for p in periods:
        def get_num(key):
            v = None
            if key and key in data and p in data[key]:
                v = data[key][p]
            return v
        cfo = get_num(keymap["CFO"])
        cfi = get_num(keymap["CFI"])
        cff = get_num(keymap["CFF"])
        reported = get_num(keymap["NET_reported"])
        def ensure_num(x):
            if isinstance(x, (int,float)) and not isinstance(x, bool):
                return int(x) if isinstance(x, np.integer) or (isinstance(x, int) and float(x).is_integer()) else x
            return x
        cfo = ensure_num(cfo); cfi = ensure_num(cfi); cff = ensure_num(cff); reported = ensure_num(reported)
        computed_net = None
        if isinstance(cfo, (int,float)) and isinstance(cfi, (int,float)) and isinstance(cff, (int,float)):
            computed_net = cfo + cfi + cff
        canonical["data"]["Cash from Operating Activity"][p] = cfo
        canonical["data"]["Cash from Investing Activity"][p] = cfi
        canonical["data"]["Cash from Financing Activity"][p] = cff
        canonical["data"]["Net Cash Flow"][p] = computed_net if computed_net is not None else reported
        canonical["data"]["reported_net"][p] = reported
        diag_entry = {"period": p, "CFO": cfo, "CFI": cfi, "CFF": cff, "reported_net": reported, "computed_net": computed_net}
        if computed_net is not None and reported is not None:
            diff = computed_net - reported
            diag_entry["diff"] = diff
            if diff != 0:
                diag_entry["note"] = "mismatch: recomputed_net != reported_net"
        diag["reconciliation"].append(diag_entry)
    return canonical, diag

def extract_top_ratios(soup: BeautifulSoup) -> Tuple[Dict[str, Any], Dict[str,Any]]:
    out = {}
    diag = {"notes": []}
    ul = soup.find("ul", {"id": "top-ratios"})
    if not ul:
        diag["notes"].append("ul#top-ratios not found")
        return out, diag
    for li in ul.find_all("li", recursive=False):
        name_tag = li.find("span", {"class": "name"}) or li.find("span")
        value_tag = li.find("span", {"class": "value"}) or li.find("span", {"class": "nowrap"}) or li.find_all("span")[-1]
        name = clean_label(name_tag.get_text()) if name_tag else None
        value = clean_label(value_tag.get_text()) if value_tag else None
        converted = to_number_cell(value)
        out[name] = converted
    # add normalized current_share_price if Current Price exists
    if "Current Price" in out:
        cp = out["Current Price"]
        try:
            out["current_share_price"] = float(cp) if cp is not None else None
        except:
            try:
                out["current_share_price"] = float(str(cp).replace(",", "")) if cp is not None else None
            except:
                out["current_share_price"] = None
    return out, diag

def extract_ratios_table(html: str) -> Tuple[Optional[Dict[str,Any]], Dict[str,Any]]:
    diag = {"notes": []}
    sec = find_section_html(html, "ratios")
    if not sec:
        diag["notes"].append("section#ratios not found")
        return None, diag
    try:
        dfs = pd.read_html(StringIO(sec))
        if not dfs:
            diag["notes"].append("no tables parsed inside #ratios")
            return None, diag
        df = dfs[0].rename(columns={dfs[0].columns[0]: 'line_item'}).set_index('line_item')
        df.index = [clean_label(i) for i in df.index]
        df.columns = [clean_label(c) for c in df.columns]
        table_json = df_to_json_like(df)
        return table_json, diag
    except Exception as e:
        diag["notes"].append(f"pd.read_html failed: {e}")
        return None, diag

def extract_all(code: str) -> Dict[str, Any]:
    url = BASE.format(code=code)
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    html = r.text
    soup = BeautifulSoup(html, "lxml")

    SECTION_MAP = {
        "profit_and_loss": "profit-loss",
        "balance_sheet": "balance-sheet",
        "cash_flows": "cash-flow"
    }
    financials = {}
    full_page_tables_html = html
    for key, anchor in SECTION_MAP.items():
        block = find_section_html(html, anchor)
        try:
            df = pick_best_table(block if block else html, key, page_html_full=full_page_tables_html)
            json_piece = df_to_json_like(df)
            if key == "cash_flows":
                corrected, diag = reconcile_cashflow_section(json_piece)
                corrected["diag"] = diag
                financials[key] = corrected
            else:
                financials[key] = json_piece
        except Exception as e:
            try:
                df = pick_best_table(html, key, page_html_full=full_page_tables_html)
                json_piece = df_to_json_like(df)
                if key == "cash_flows":
                    corrected, diag = reconcile_cashflow_section(json_piece)
                    corrected["diag"] = diag
                    financials[key] = corrected
                else:
                    financials[key] = json_piece
            except Exception as e2:
                financials[key] = {"error": "parse_failed", "message": f"{e}; fallback: {e2}"}

    # extract ratios (top block + ratios table)
    ratios_obj = {}
    ratios_diag = {}
    try:
        top_ratios, diag_top = extract_top_ratios(soup)
        ratios_obj["top"] = top_ratios
        ratios_diag["top"] = diag_top
    except Exception as e:
        ratios_diag["top"] = {"error": str(e)}
    try:
        ratios_table, diag_table = extract_ratios_table(html)
        ratios_obj["table"] = ratios_table
        ratios_diag["table"] = diag_table
    except Exception as e:
        ratios_diag["table"] = {"error": str(e)}

    financials["ratios"] = {"units": "mixed", "data": ratios_obj, "diag": ratios_diag}

    final = {"source": url, "units": "Rs. Crores", "extracted_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"), "financials": financials}
    return final

# new: public function to get financials (returns dict, no disk writes)
def get_financials(code: str) -> Dict[str, Any]:
    """
    Synchronous extractor. Returns parsed JSON-like dict for the given company code.
    Example: get_financials("ITCHOTELS")
    """
    return extract_all(code)

def main_print():
    if len(sys.argv) < 2:
        print("Usage: python extract_screener_financials.py <COMPANY_CODE>", file=sys.stderr)
        sys.exit(1)
    code = sys.argv[1].strip()
    out = get_financials(code)
    # print to stdout (no file saves)
    print(json.dumps(out, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main_print()
