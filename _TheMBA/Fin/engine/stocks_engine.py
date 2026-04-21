import pandas as pd
import numpy as np
import yfinance as yf



# =====================================
# FIND STOCK TABLE
# =====================================

def find_stock_table(portfolio):

    for key in portfolio:

        name = key.lower()

        if any(x in name for x in [

            "stock",

            "equity",

            "overview"

        ]):

            df = portfolio[key]

            if isinstance(df, pd.DataFrame):

                return df

    return None



# =====================================
# FETCH STOCK DATA
# =====================================

def fetch_stock_data(ticker):

    try:

        stock = yf.Ticker(ticker)

        info = stock.info

        hist = stock.history(

            period="2y"

        )

        if hist.empty:

            return None


        hist.reset_index(inplace=True)


        # =================================
        # RETURNS
        # =================================

        hist["Return"] = (

            hist["Close"]

            .pct_change()

        )


        hist["Peak"] = (

            hist["Close"]

            .cummax()

        )


        hist["Drawdown"] = (

            hist["Close"]

            - hist["Peak"]

        ) / hist["Peak"]


        for w in [30, 90, 180]:

            if len(hist) > w:

                hist[f"Rolling_{w}"] = (

                    hist["Close"]

                    .pct_change(w)

                )


        fundamentals = {

            "marketCap":

                info.get("marketCap"),

            "trailingPE":

                info.get("trailingPE"),

            "priceToBook":

                info.get("priceToBook"),

            "returnOnEquity":

                info.get("returnOnEquity"),

            "profitMargins":

                info.get("profitMargins"),

            "revenueGrowth":

                info.get("revenueGrowth"),

            "debtToEquity":

                info.get("debtToEquity"),

            "dividendYield":

                info.get("dividendYield"),

            "beta":

                info.get("beta"),

            "sector":

                info.get("sector"),

            "fiftyTwoWeekHigh":

                info.get("fiftyTwoWeekHigh"),

            "fiftyTwoWeekLow":

                info.get("fiftyTwoWeekLow")

        }


        return {

            "history": hist,

            "fundamentals": fundamentals

        }


    except Exception as e:

        print("Stock fetch error:", ticker, e)

        return None



# =====================================
# MAIN ENGINE
# =====================================

def run_stock_engine(portfolio):

    stock_df = find_stock_table(

        portfolio

    )

    if stock_df is None:

        print("Stock table not found")

        return {}


    ticker_col = None

    for col in [

        "Company_Name",

        "Ticker",

        "Symbol"

    ]:

        if col in stock_df.columns:

            ticker_col = col
            break


    if ticker_col is None:

        print("Ticker column not found")

        return {}


    stock_data = {}

    allocation_df = stock_df.copy()


    for i, row in stock_df.iterrows():

        ticker = str(

            row[ticker_col]

        ).strip()


        # NSE adjustment

        if ".NS" not in ticker:

            ticker = ticker + ".NS"


        print("Fetching stock:", ticker)


        data = fetch_stock_data(

            ticker

        )


        if data is None:

            continue


        stock_data[ticker] = data


    if len(stock_data) == 0:

        print("No stock data fetched")

        return {}


    return {

        "allocation": allocation_df,

        "stock_data": stock_data

    }