import pandas as pd
import numpy as np
from scipy.optimize import newton


# =========================================
# HISTORY STANDARDIZER
# =========================================

def standardize_history(df):

    if df is None or df.empty:
        return None

    df = df.copy()

    df = df.dropna(axis=1, how="all")

    # Detect Date column

    date_col = None

    for col in df.columns:

        sample = (
            df[col]
            .astype(str)
            .head(10)
        )

        if sample.str.contains(
            r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
            regex=True
        ).sum() > 0:

            date_col = col
            break

    if date_col is None:
        raise Exception("Date column not found")

    df = df.rename(
        columns={
            date_col: "Date"
        }
    )

    df["Date"] = pd.to_datetime(
        df["Date"],
        dayfirst=True,
        errors="coerce"
    )

    df = df.dropna(subset=["Date"])

    # Detect Total Value

    numeric_cols = df.select_dtypes(
        include="number"
    ).columns

    if "Total_Value" not in df.columns:

        if len(numeric_cols) == 0:
            raise Exception("Total_Value not found")

        df = df.rename(
            columns={
                numeric_cols[-1]: "Total_Value"
            }
        )

    df = df.sort_values(
        "Date"
    ).reset_index(drop=True)

    return df


# =========================================
# DAILY RETURNS
# =========================================

def calculate_daily_returns(history_daily):

    df = standardize_history(
        history_daily
    )

    if df is None or len(df) < 2:
        return df

    df["Daily_Return"] = (
        df["Total_Value"]
        .pct_change()
        .fillna(0)
    )

    return df


# =========================================
# MONTHLY RETURNS
# =========================================

def calculate_monthly_returns(history_monthly):

    df = standardize_history(
        history_monthly
    )

    if df is None or len(df) < 2:
        return df

    df["Monthly_Return"] = (
        df["Total_Value"]
        .pct_change()
        .fillna(0)
    )

    return df


# =========================================
# CAGR
# =========================================

def calculate_cagr(history_monthly):

    df = standardize_history(
        history_monthly
    )

    if df is None or len(df) < 2:
        return None

    start_value = df["Total_Value"].iloc[0]
    end_value = df["Total_Value"].iloc[-1]

    start_date = df["Date"].iloc[0]
    end_date = df["Date"].iloc[-1]

    years = (
        (end_date - start_date)
        .days / 365.25
    )

    if years <= 0:
        return None

    cagr = (
        (end_value / start_value)
        ** (1 / years)
    ) - 1

    return cagr


# =========================================
# XIRR
# =========================================

def calculate_xirr(trades, history_daily):

    if trades is None or trades.empty:
        return None

    history_daily = standardize_history(
        history_daily
    )

    if history_daily is None:
        return None

    cashflows = []
    dates = []

    for _, row in trades.iterrows():

        amount = row.get("Amount")
        date = row.get("Date")

        if pd.isna(amount) or pd.isna(date):
            continue

        cashflows.append(-amount)
        dates.append(date)

    final_value = (
        history_daily
        .iloc[-1]["Total_Value"]
    )

    final_date = (
        history_daily
        .iloc[-1]["Date"]
    )

    cashflows.append(final_value)
    dates.append(final_date)

    try:

        def xirr_func(rate):

            result = 0

            t0 = dates[0]

            for c, d in zip(
                cashflows,
                dates
            ):

                days = (
                    d - t0
                ).days

                result += (
                    c /
                    ((1 + rate) **
                     (days / 365))
                )

            return result

        rate = newton(
            xirr_func,
            0.1
        )

        return rate

    except:

        return None


# =========================================
# TWR
# =========================================

def calculate_twr(history_daily):

    df = standardize_history(
        history_daily
    )

    if df is None or len(df) < 2:
        return None

    df["Return"] = (
        df["Total_Value"]
        .pct_change()
        .fillna(0)
    )

    twr = (
        (1 + df["Return"])
        .prod()
    ) - 1

    return twr


# =========================================
# ROLLING RETURNS
# =========================================

def calculate_rolling_returns(
    history_daily,
    window=30
):

    df = standardize_history(
        history_daily
    )

    if df is None or len(df) < window:
        return df

    df["Daily_Return"] = (
        df["Total_Value"]
        .pct_change()
    )

    df["Rolling_Return"] = (
        df["Daily_Return"]
        .rolling(window)
        .mean()
    )

    return df


# =========================================
# GROWTH CURVE
# =========================================

def calculate_growth_curve(history_daily):

    df = standardize_history(
        history_daily
    )

    if df is None or len(df) < 1:
        return df

    base_value = (
        df["Total_Value"]
        .iloc[0]
    )

    df["Growth_Index"] = (
        df["Total_Value"]
        / base_value
    )

    return df


# =========================================
# MASTER ENGINE
# =========================================

def run_returns_engine(portfolio):

    history_daily = portfolio.get(
        "history_daily"
    )

    history_monthly = portfolio.get(
        "history_monthly"
    )

    trades = portfolio.get(
        "Trades"
    )

    daily_returns = calculate_daily_returns(
        history_daily
    )

    monthly_returns = calculate_monthly_returns(
        history_monthly
    )

    cagr = calculate_cagr(
        history_monthly
    )

    xirr = calculate_xirr(
        trades,
        history_daily
    )

    twr = calculate_twr(
        history_daily
    )

    rolling_returns = calculate_rolling_returns(
        history_daily
    )

    growth_curve = calculate_growth_curve(
        history_daily
    )

    return {

        "daily_returns": daily_returns,
        "monthly_returns": monthly_returns,
        "CAGR": cagr,
        "XIRR": xirr,
        "TWR": twr,
        "rolling_returns": rolling_returns,
        "growth_curve": growth_curve

    }