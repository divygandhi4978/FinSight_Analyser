import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime

# -------------------------------
# TARGET COMPANIES
# -------------------------------

TICKERS = [
    "APOLLOHOSP.NS",
    "FORTIS.NS",
    "MAXHEALTH.NS",
    "NH.NS",
    "RAINBOW.NS"
]

# -------------------------------
# UTILITY FUNCTIONS
# -------------------------------

def dataframe_to_dict(df):
    """
    Convert pandas DataFrame into JSON-safe dictionary.
    """
    if df is None or df.empty:
        return {}

    df = df.replace({np.nan: None})
    return df.to_dict()


def series_to_list(series):
    """
    Convert pandas Series into list format.
    """
    if series is None or series.empty:
        return []

    return [
        {
            "date": str(idx),
            "value": None if pd.isna(val) else float(val)
        }
        for idx, val in series.items()
    ]


# -------------------------------
# QoQ GROWTH CALCULATION
# -------------------------------

def compute_qoq(financials_q):
    """
    Compute QoQ growth for Revenue & Net Income.
    """

    result = {}

    try:
        if financials_q is None or financials_q.empty:
            return result

        df = financials_q.T

        if "Total Revenue" in df.columns:
            revenue = df["Total Revenue"]

            qoq = revenue.pct_change()

            result["revenue_qoq"] = [
                None if pd.isna(x) else float(x)
                for x in qoq
            ]

        if "Net Income" in df.columns:
            profit = df["Net Income"]

            qoq = profit.pct_change()

            result["net_income_qoq"] = [
                None if pd.isna(x) else float(x)
                for x in qoq
            ]

    except Exception:
        pass

    return result


# -------------------------------
# MAIN DATA COLLECTION
# -------------------------------

def collect_company_data(ticker_symbol):

    ticker = yf.Ticker(ticker_symbol)

    company_data = {}

    company_data["ticker"] = ticker_symbol

    # -------------------------------
    # BASIC INFO
    # -------------------------------

    try:
        info = ticker.info
        company_data["info"] = info
    except:
        company_data["info"] = {}

    # -------------------------------
    # PRICE DATA (12 MONTHS)
    # -------------------------------

    try:
        price_df = ticker.history(period="12mo")

        company_data["price_data_12m"] = (
            price_df
            .reset_index()
            .replace({np.nan: None})
            .to_dict(orient="records")
        )

    except:
        company_data["price_data_12m"] = []

    # -------------------------------
    # FINANCIAL STATEMENTS
    # -------------------------------

    try:
        fin_annual = ticker.financials
        company_data["financials_annual"] = dataframe_to_dict(fin_annual)
    except:
        company_data["financials_annual"] = {}

    try:
        fin_q = ticker.quarterly_financials
        company_data["financials_quarterly"] = dataframe_to_dict(fin_q)
    except:
        fin_q = None
        company_data["financials_quarterly"] = {}

    # -------------------------------
    # BALANCE SHEET
    # -------------------------------

    try:
        bs = ticker.balance_sheet
        company_data["balance_sheet"] = dataframe_to_dict(bs)
    except:
        company_data["balance_sheet"] = {}

    try:
        bs_q = ticker.quarterly_balance_sheet
        company_data["balance_sheet_quarterly"] = dataframe_to_dict(bs_q)
    except:
        company_data["balance_sheet_quarterly"] = {}

    # -------------------------------
    # CASH FLOW
    # -------------------------------

    try:
        cf = ticker.cashflow
        company_data["cashflow"] = dataframe_to_dict(cf)
    except:
        company_data["cashflow"] = {}

    try:
        cf_q = ticker.quarterly_cashflow
        company_data["cashflow_quarterly"] = dataframe_to_dict(cf_q)
    except:
        company_data["cashflow_quarterly"] = {}

    # -------------------------------
    # EARNINGS
    # -------------------------------

    try:
        earnings = ticker.earnings
        company_data["earnings"] = dataframe_to_dict(earnings)
    except:
        company_data["earnings"] = {}

    try:
        earnings_q = ticker.quarterly_earnings
        company_data["earnings_quarterly"] = dataframe_to_dict(earnings_q)
    except:
        company_data["earnings_quarterly"] = {}

    # -------------------------------
    # DIVIDENDS
    # -------------------------------

    try:
        div = ticker.dividends
        company_data["dividends"] = series_to_list(div)
    except:
        company_data["dividends"] = []

    # -------------------------------
    # RECOMMENDATIONS
    # -------------------------------

    try:
        rec = ticker.recommendations
        company_data["recommendations"] = dataframe_to_dict(rec)
    except:
        company_data["recommendations"] = {}

    # -------------------------------
    # HOLDERS
    # -------------------------------

    try:
        inst = ticker.institutional_holders
        company_data["institutional_holders"] = dataframe_to_dict(inst)
    except:
        company_data["institutional_holders"] = {}

    try:
        major = ticker.major_holders
        company_data["major_holders"] = dataframe_to_dict(major)
    except:
        company_data["major_holders"] = {}

    # -------------------------------
    # QoQ CALCULATIONS
    # -------------------------------

    company_data["qoq_growth"] = compute_qoq(fin_q)

    return company_data


# -------------------------------
# MASTER RUN FUNCTION
# -------------------------------

def run_collection():

    master_data = {}

    for ticker in TICKERS:

        print(f"Collecting data for {ticker}...")

        data = collect_company_data(ticker)

        master_data[ticker] = data

    timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    file_name = f"healthcare_yfinance_dump_{timestamp}.json"

    with open(file_name, "w") as f:
        json.dump(master_data, f, indent=4)

    print("\nData Collection Complete")
    print(f"Saved to: {file_name}")

    return master_data


# -------------------------------
# RUN
# -------------------------------

if __name__ == "__main__":
    data = run_collection()