import pandas as pd
import requests
from io import StringIO


# =====================================
# CONFIG
# =====================================

USE_GOOGLE_SHEET = True

GOOGLE_SHEET_ID = "1XaEHgfnZ4nn3-Vvja05WdGNpdwsZTlGpk8gXAirAI5E"

LOCAL_EXCEL_FILE = "TheWealth.xlsx"


CORE_TABS = [
    "All_Investment",
    "Overview",
    "History",
    "Monthly_History",
    "Trades",
    "MutualFunds",
    "FDs",
    "kvp",
    "Overview_Snapshot"
]


# =====================================
# FETCH TAB (GOOGLE)
# =====================================

def fetch_google_tab(tab_name):

    url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{GOOGLE_SHEET_ID}"
        f"/gviz/tq?tqx=out:csv&sheet={tab_name}"
    )

    try:

        response = requests.get(
            url,
            timeout=10
        )

        if response.status_code != 200:

            print(f"FAILED LOAD: {tab_name}")

            return None

        text = response.text

        # Detect HTML error page
        if "<html" in text.lower():

            print(f"HTML RESPONSE: {tab_name}")

            return None

        df = pd.read_csv(
            StringIO(text),
            header=0
        )

        if df.empty:

            print(f"EMPTY TAB: {tab_name}")

            return None

        return df

    except Exception as e:

        print(
            f"ERROR FETCHING {tab_name}:",
            e
        )

        return None

# =====================================
# FETCH TAB (EXCEL)
# =====================================

def fetch_excel_tab(tab_name):

    try:

        df = pd.read_excel(
            LOCAL_EXCEL_FILE,
            sheet_name=tab_name,
            header=None
        )

        return df

    except:

        return None


# =====================================
# FETCH UNIVERSAL
# =====================================

def fetch_raw_tab(tab_name):

    if USE_GOOGLE_SHEET:

        df = fetch_google_tab(tab_name)

        if df is not None:
            return df

    return fetch_excel_tab(tab_name)


# =====================================
# HEADER DETECTION
# =====================================

def detect_header_row(df):

    max_scan = min(15, len(df))

    for i in range(max_scan):

        row = df.iloc[i]

        values = (
            row
            .fillna("")
            .astype(str)
            .str.lower()
            .tolist()
        )

        if any("date" in v for v in values):
            return i

        if any("ticker" in v for v in values):
            return i

        if any("fund" in v for v in values):
            return i

        if any("total" in v for v in values):
            return i

    return 0


# =====================================
# CLEAN TAB
# =====================================

def clean_table(df):

    header_row = detect_header_row(df)

    headers = (
        df.iloc[header_row]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.replace(" ", "_")
    )

    df.columns = headers

    df = df.iloc[header_row + 1 :]

    df = df.dropna(
        how="all"
    )

    df = df.reset_index(drop=True)

    return df


# =====================================
# LOAD TAB
# =====================================

def load_tab(tab_name):

    raw = fetch_raw_tab(tab_name)

    if raw is None:

        print(f"ERROR: {tab_name} fetch failed")

        return None

    df = clean_table(raw)

    if df is None or df.empty:

        print(f"WARNING: {tab_name} empty")

        return None

    return df


# =====================================
# PROCESS HISTORY
# =====================================

def process_history(df):

    if df is None:
        return None

    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.replace(" ", "_")
    )

    # Detect date column

    date_col = None

    for col in df.columns:

        if "date" in col.lower():
            date_col = col
            break

    if date_col is None:
        return None

    df[date_col] = pd.to_datetime(
        df[date_col],
        dayfirst=True,
        errors="coerce"
    )

    df = df.dropna(
        subset=[date_col]
    )

    # Detect total column

    total_col = None

    for col in df.columns:

        if "total" in col.lower():
            total_col = col
            break

    if total_col is None:
        return None

    df = df.rename(
        columns={
            date_col: "Date",
            total_col: "Total_Value"
        }
    )

    df["Total_Value"] = (
        df["Total_Value"]
        .astype(float)
    )

    df = df.sort_values("Date")

    df["Daily_Return"] = (
        df["Total_Value"]
        .pct_change()
        .fillna(0)
    )

    return df


# =====================================
# DETECT STOCK TABS
# =====================================
def detect_stock_tabs(portfolio):

    # USE SNAPSHOT — NOT OVERVIEW

    overview = portfolio.get("Overview_Snapshot")

    if overview is None:

        print("ERROR: Overview_Snapshot missing")

        return []

    if "Company_Name" not in overview.columns:

        print("ERROR: Company_Name missing")

        return []

    companies = (
        overview["Company_Name"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    stock_tabs = []

    print("\nDetecting Stock Tabs...\n")

    for company in companies:

        df = fetch_raw_tab(company)

        if df is not None:

            print(f"FOUND: {company}")

            stock_tabs.append(company)

        else:

            print(f"NOT FOUND: {company}")

    return stock_tabs

# =====================================
# MAIN INITIALIZER
# =====================================
def initialize_portfolio_data():

    portfolio = {}

    print("\nLoading Raw Portfolio Data...\n")

    # ---------------------------------
    # LOAD CORE TABS
    # ---------------------------------

    for tab in CORE_TABS:

        df = load_tab(tab)

        if df is None:

            print(f"WARNING: {tab} not loaded")

        else:

            portfolio[tab] = df

    # ---------------------------------
    # PROCESS HISTORY
    # ---------------------------------

    if "History" in portfolio:

        hist_daily = process_history(
            portfolio["History"]
        )

        if hist_daily is not None:

            portfolio["history_daily"] = hist_daily

        else:

            print("WARNING: history_daily failed")

    else:

        print("WARNING: History tab missing")


# ---------------------------------
# RENAME SNAPSHOT → OVERVIEW
# ---------------------------------

    if "Overview_Snapshot" in portfolio:

        portfolio["Overview"] = (
            portfolio.pop("Overview_Snapshot")
        )
        
    if "Monthly_History" in portfolio:

        hist_monthly = process_history(
            portfolio["Monthly_History"]
        )

        if hist_monthly is not None:

            portfolio["history_monthly"] = hist_monthly

        else:

            print("WARNING: history_monthly failed")

    else:

        print("WARNING: Monthly_History tab missing")



    # ---------------------------------
    # REMOVE STOCK AUTO-DETECTION
    # (Not needed for your system)
    # ---------------------------------

    # -------------------------
# LOAD STOCK TABS
# -------------------------

    stock_tabs = {}

    tickers = detect_stock_tabs(portfolio)

    for ticker in tickers:

        df = load_tab(ticker)

        if df is not None:

            stock_tabs[ticker] = df

    portfolio["stocks"] = stock_tabs



    # ---------------------------------
    # SAFE DEBUG SUMMARY
    # ---------------------------------

    print("\n========== DATA SUMMARY ==========")

    for key in portfolio:

        value = portfolio[key]

        if value is None:

            print(f"{key}: None")

        elif isinstance(value, dict):

            print(
                f"{key}: {len(value)} stock tabs"
            )

        else:

            print(
                f"{key}: {value.shape}"
            )

    print("==================================\n")

    return portfolio