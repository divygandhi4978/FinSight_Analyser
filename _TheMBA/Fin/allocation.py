import pandas as pd


# =====================================
# RUN ALLOCATION ENGINE
# =====================================

def run_allocation_engine(portfolio):

    result = {}

    # =========================
    # SEGMENT ALLOCATION
    # =========================

    overview = portfolio.get("Overview")

    if isinstance(overview, pd.DataFrame):

        df = overview.copy()

        if "Current_Value" in df.columns:

            total = df["Current_Value"].sum()

            if total > 0:

                df["Weight"] = (

                    df["Current_Value"]

                    / total

                )

                segment = (

                    df.groupby("Segment")

                    ["Weight"]

                    .sum()

                    .reset_index()

                )

                segment.columns = [

                    "Segment",

                    "Segment_%"

                ]

                result["segment_allocation"] = segment


    # =========================
    # STOCK ALLOCATION
    # =========================

    if isinstance(overview, pd.DataFrame):

        df = overview.copy()

        if "Current_Value" in df.columns:

            total = df["Current_Value"].sum()

            if total > 0:

                df["Stock_%"] = (

                    df["Current_Value"]

                    / total

                )

                stock_df = df[

                    [

                        "Company_Name",

                        "Stock_%"

                    ]

                ]

                result["stock_allocation"] = (

                    stock_df

                    .sort_values(

                        "Stock_%",

                        ascending=False

                    )

                )


    return result