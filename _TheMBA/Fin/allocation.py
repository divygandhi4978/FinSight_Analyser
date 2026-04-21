import pandas as pd


# ==========================
# SAFE NUMERIC CLEAN
# ==========================

def clean_numeric(series):

    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("₹", "", regex=False)
        .str.replace("%", "", regex=False),
        errors="coerce"
    )


# ==========================
# MAIN ALLOCATION ENGINE
# ==========================

def run_allocation_engine(portfolio):

    result = {}

    overview = portfolio.get("Overview")
    all_inv = portfolio.get("All_Investment")


    # ==========================
    # STOCK ALLOCATION
    # ==========================

    if overview is not None and not overview.empty:

        stock_df = overview.copy()

        if "Total_Value" in stock_df.columns:

            stock_df["Total_Value"] = clean_numeric(
                stock_df["Total_Value"]
            )

            stock_df = stock_df.dropna(
                subset=["Total_Value"]
            )

            total_stock_value = (
                stock_df["Total_Value"].sum()
            )

            if total_stock_value > 0:

                stock_df["Stock_%"] = (

                    stock_df["Total_Value"]
                    / total_stock_value
                    * 100

                )

                stock_df = stock_df.sort_values(
                    "Stock_%",
                    ascending=False
                )

        result["stock_allocation"] = stock_df



    # ==========================
    # SEGMENT ALLOCATION
    # ==========================

    if all_inv is not None and not all_inv.empty:

        seg_df = all_inv.copy()

        seg_df = seg_df.iloc[:, :2]

        seg_df.columns = [
            "Segment",
            "Value"
        ]

        seg_df["Value"] = clean_numeric(
            seg_df["Value"]
        )

        seg_df = seg_df.dropna(
            subset=["Value"]
        )

        total_value = seg_df["Value"].sum()

        if total_value > 0:

            seg_df["Segment_%"] = (

                seg_df["Value"]
                / total_value
                * 100

            )

            seg_df = seg_df.sort_values(
                "Segment_%",
                ascending=False
            )

        result["segment_allocation"] = seg_df


    return result