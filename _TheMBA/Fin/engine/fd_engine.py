import pandas as pd
import numpy as np



# =====================================
# FIND FD TABLE
# =====================================

def find_fd_table(portfolio):

    for key in portfolio:

        name = key.lower()

        if any(x in name for x in [

            "fd",

            "fixed",

            "deposit"

        ]):

            df = portfolio[key]

            if isinstance(df, pd.DataFrame):

                return df

    return None



# =====================================
# MAIN FD ENGINE
# =====================================

def run_fd_engine(portfolio):

    fd_df = find_fd_table(portfolio)

    if fd_df is None:

        print("FD table not found")

        return {}


    df = fd_df.copy()


    # Convert dates

    if "Maturity_Date" in df.columns:

        df["Maturity_Date"] = pd.to_datetime(
            df["Maturity_Date"],
            errors="coerce"
        )


    today = pd.Timestamp.today()


    # =====================================
    # DAYS TO MATURITY
    # =====================================

    df["Days_Remaining"] = (

        df["Maturity_Date"]

        - today

    ).dt.days


    df["Years_Remaining"] = (

        df["Days_Remaining"] / 365

    )


    # =====================================
    # TOTAL VALUE
    # =====================================

    total_value = df["Principal_Amount"].sum()


    # =====================================
    # WEIGHTED INTEREST RATE
    # =====================================

    weighted_rate = (

        (df["Principal_Amount"]

        * df["Interest_Rate_Pct"]).sum()

        / total_value

    )


    # =====================================
    # WEIGHTED TENURE
    # =====================================

    weighted_tenure = (

        (df["Principal_Amount"]

        * df["Years_Remaining"]).sum()

        / total_value

    )


    # =====================================
    # MATURITY BUCKETS
    # =====================================

    bins = [

        0,

        90,

        180,

        365,

        730,

        1825,

        3650

    ]


    labels = [

        "0–3M",

        "3–6M",

        "6–12M",

        "1–2Y",

        "2–5Y",

        "5Y+"

    ]


    df["Maturity_Bucket"] = pd.cut(

        df["Days_Remaining"],

        bins=bins,

        labels=labels

    )


    maturity_dist = (

        df.groupby("Maturity_Bucket")

        ["Principal_Amount"]

        .sum()

        .reset_index()

    )


    # =====================================
    # BANK EXPOSURE
    # =====================================

    if "Bank_Post_Office" in df.columns:

        bank_dist = (

            df.groupby(

                "Bank_Post_Office"

            )

            ["Principal_Amount"]

            .sum()

            .reset_index()

        )

    else:

        bank_dist = pd.DataFrame()


    return {

        "fd_df": df,

        "total_value": total_value,

        "weighted_rate": weighted_rate,

        "weighted_tenure": weighted_tenure,

        "maturity_dist": maturity_dist,

        "bank_dist": bank_dist

    }