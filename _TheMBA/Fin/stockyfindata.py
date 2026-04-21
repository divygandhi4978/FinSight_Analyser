import yfinance as yf
import pandas as pd
import time


# -------------------------------
# RETRY WRAPPER
# -------------------------------

def retry_call(func, retries=3):

    for i in range(retries):

        try:
            return func()

        except Exception as e:

            print(f"Retry {i+1} failed:", e)

            time.sleep(1)

    print("All retries failed.")
    return None


# -------------------------------
# GET HISTORY
# -------------------------------

def get_history(
        symbol,
        period="1y",
        interval="1d"
):

    def call():

        ticker = yf.Ticker(symbol)

        df = ticker.history(
            period=period,
            interval=interval
        )

        return df

    return retry_call(call)


# -------------------------------
# MULTI STOCK HISTORY
# -------------------------------

def get_multi_history(
        symbols,
        period="1y",
        interval="1d"
):

    def call():

        df = yf.download(
            tickers=symbols,
            period=period,
            interval=interval,
            group_by="ticker"
        )

        return df

    return retry_call(call)


# -------------------------------
# LATEST QUOTE
# -------------------------------

def get_quote(symbol):

    def call():

        ticker = yf.Ticker(symbol)

        info = ticker.info

        return {
            "symbol": symbol,
            "price": info.get("currentPrice"),
            "marketCap": info.get("marketCap"),
            "peRatio": info.get("trailingPE"),
            "sector": info.get("sector")
        }

    return retry_call(call)


# -------------------------------
# DIVIDENDS
# -------------------------------

def get_dividends(symbol):

    def call():

        ticker = yf.Ticker(symbol)

        return ticker.dividends

    return retry_call(call)


# -------------------------------
# FINANCIAL STATEMENTS
# -------------------------------

def get_financials(symbol):

    def call():

        ticker = yf.Ticker(symbol)

        return {
            "income_statement": ticker.financials,
            "balance_sheet": ticker.balance_sheet,
            "cashflow": ticker.cashflow
        }

    return retry_call(call)


# ===============================
# MAIN RUNNER
# ===============================

if __name__ == "__main__":

    symbol = "RELIANCE.NS"

    print("\n--- HISTORY ---")

    history = get_history(
        symbol,
        period="1y"
    )

    if history is not None:
        print(history.head())


    print("\n--- MULTI STOCK ---")

    multi = get_multi_history(
        ["RELIANCE.NS", "TCS.NS"]
    )

    if multi is not None:
        print(multi.head())


    print("\n--- QUOTE ---")

    quote = get_quote(symbol)

    if quote is not None:
        print(quote)


    print("\n--- DIVIDENDS ---")

    dividends = get_dividends(symbol)

    if dividends is not None:
        print(dividends.tail())


    print("\n--- FINANCIALS ---")

    financials = get_financials(symbol)

    if financials is not None:

        print(
            financials["income_statement"].head()
        )