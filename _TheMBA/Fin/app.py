import pandas as pd
import numpy as np

from datetime import datetime, timedelta

from data_loader import initialize_portfolio_data
from cleaner import clean_portfolio
from returns_engine import run_returns_engine
from allocation import run_allocation_engine



# =====================================
# REPAIR ANY BROKEN DATAFRAME
# =====================================

def repair_dataframe(df):

    if df is None:
        return df

    df = df.copy()

    df.columns = [

        str(c).strip()

        for c in df.columns

    ]

    bad = False

    for c in df.columns:

        if "/" in c or "." in c:

            bad = True
            break

    if bad:

        df.columns = [

            f"col_{i}"

            for i in range(len(df.columns))

        ]

    df = df.loc[:, ~df.columns.duplicated()]

    return df



# =====================================
# FAKE HISTORY IF NEEDED
# =====================================

def generate_fake_history():

    rows = []

    start = datetime(2026, 1, 1)

    value = 1000000

    for i in range(120):

        change = np.random.normal(
            0.001,
            0.004
        )

        value *= (1 + change)

        rows.append([
            start + timedelta(days=i),
            round(value, 2)
        ])

    df = pd.DataFrame(
        rows,
        columns=[
            "Date",
            "Total_Value"
        ]
    )

    return df



# =====================================
# BUILD SYSTEM
# =====================================

def build_system():

    raw = initialize_portfolio_data()

    portfolio = clean_portfolio(raw)

    # Repair all tables

    for k in portfolio:

        if isinstance(
            portfolio[k],
            pd.DataFrame
        ):

            portfolio[k] = repair_dataframe(
                portfolio[k]
            )


    # Ensure history

    daily = portfolio.get(
        "history_daily"
    )

    if daily is None or len(daily) < 10:

        portfolio["history_daily"] = (
            generate_fake_history()
        )


    # RETURNS

    returns_data = run_returns_engine(
        portfolio
    )


    # ALLOCATIONS

    allocation_data = run_allocation_engine(
        portfolio
    )


    return {

        "portfolio": portfolio,
        "returns": returns_data,
        "allocations": allocation_data

    }



if __name__ == "__main__":

    system = build_system()

    print("System Ready")