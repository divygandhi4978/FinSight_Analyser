import pandas as pd
import numpy as np


def run_performance_engine(portfolio):

    if "history_daily" not in portfolio:

        print("No history_daily found")

        return {}


    df = portfolio["history_daily"].copy()

    if df is None or len(df) < 2:

        print("history_daily empty")

        return {}


    # Ensure Date

    df["Date"] = pd.to_datetime(df["Date"])

    df = df.sort_values("Date")


    # =========================
    # DAILY RETURNS
    # =========================

    df["Daily_Return"] = (

        df["Total_Value"]

        .pct_change()

    )


    # =========================
    # ROLLING RETURNS
    # =========================

    windows = [30, 90, 180]

    for w in windows:

        if len(df) > w:

            df[f"Rolling_{w}"] = (

                df["Total_Value"]

                .pct_change(w)

            )


    # =========================
    # DRAWDOWN
    # =========================

    df["Running_Max"] = (

        df["Total_Value"]

        .cummax()

    )

    df["Drawdown"] = (

        df["Total_Value"]

        - df["Running_Max"]

    ) / df["Running_Max"]


    # =========================
    # METRICS
    # =========================

    start_value = df["Total_Value"].iloc[0]

    end_value = df["Total_Value"].iloc[-1]

    days = (

        df["Date"].iloc[-1]

        - df["Date"].iloc[0]

    ).days


    years = days / 365 if days > 0 else 0


    if years > 0:

        cagr = (

            (end_value / start_value)

            ** (1 / years)

        ) - 1

    else:

        cagr = 0


    volatility = (

        df["Daily_Return"]

        .std()

        * np.sqrt(252)

    )


    max_dd = df["Drawdown"].min()


    metrics = pd.DataFrame({

        "Metric": [

            "CAGR",

            "Volatility",

            "Max Drawdown"

        ],

        "Value": [

            cagr,

            volatility,

            max_dd

        ]

    })


    return {

        "performance_df": df,

        "metrics": metrics

    }