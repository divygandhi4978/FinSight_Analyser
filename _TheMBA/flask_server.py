import yfinance as yf
import pandas as pd
import numpy as np
import json

from flask import Flask, jsonify
from datetime import datetime

app = Flask(__name__)

# -------------------------
# TARGET STOCKS
# -------------------------

TICKERS = [
    "APOLLOHOSP.NS",
    "FORTIS.NS",
    "MAXHEALTH.NS",
    "NH.NS",
    "RAINBOW.NS"
]

# -------------------------
# SAFE CONVERTER
# -------------------------

def safe_value(val):

    if isinstance(val, (pd.Timestamp, datetime)):
        return val.strftime("%Y-%m")

    if pd.isna(val):
        return None

    if isinstance(val, (np.integer,)):
        return int(val)

    if isinstance(val, (np.floating,)):
        return float(val)

    return val


# -------------------------
# COMPANY INFO CLEAN
# -------------------------

def get_company_info(ticker):

    info = ticker.info

    return {
        "website": info.get("website"),
        "longBusinessSummary": info.get("longBusinessSummary"),
        "companyOfficers": info.get("companyOfficers")
    }


# -------------------------
# MARKET DATA CLEAN
# -------------------------

def get_market_data(ticker):

    info = ticker.info

    return {
        "previousClose": info.get("previousClose"),
        "dividendYield": info.get("dividendYield"),
        "regularMarketPrice": info.get("regularMarketPrice")
    }


# -------------------------
# QUARTERLY CLEAN
# -------------------------

def get_quarterly_data(ticker):

    try:

        fin_q = ticker.quarterly_financials

        if fin_q is None or fin_q.empty:
            return []

        df = fin_q.T

        records = []

        # last 12 quarters only
        df = df.tail(12)

        for idx, row in df.iterrows():

            record = {
                "quarter": safe_value(idx),

                "revenue":
                    safe_value(
                        row.get("Total Revenue")
                    ),

                "net_income":
                    safe_value(
                        row.get("Net Income")
                    ),

                "operating_income":
                    safe_value(
                        row.get("Operating Income")
                    ),

                "gross_profit":
                    safe_value(
                        row.get("Gross Profit")
                    )
            }

            records.append(record)

        return records

    except Exception as e:

        print("Quarter error:", e)

        return []


# -------------------------
# MASTER STRUCTURED OBJECT
# -------------------------

def build_company_dataset(ticker_symbol):

    ticker = yf.Ticker(ticker_symbol)

    dataset = {}

    dataset["ticker"] = ticker_symbol

    dataset["company_info"] = get_company_info(ticker)

    dataset["market_data"] = get_market_data(ticker)

    dataset["quarterly_results"] = get_quarterly_data(ticker)

    return dataset


# -------------------------
# COLLECT ALL
# -------------------------

def collect_all():

    master = {}

    for t in TICKERS:

        print("Processing:", t)

        master[t] = build_company_dataset(t)

    return master


# -------------------------
# API ROUTES
# -------------------------

@app.route("/health")

def health():

    return jsonify({
        "status": "running",
        "time": datetime.now().isoformat()
    })


@app.route("/company/<ticker>")

def get_company(ticker):

    data = build_company_dataset(ticker)

    return jsonify(data)


@app.route("/all")

def get_all():

    data = collect_all()

    return jsonify(data)


# -------------------------
# RUN SERVER
# -------------------------

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )