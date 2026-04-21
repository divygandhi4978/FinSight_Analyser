import pandas as pd


def compute_portfolio_overview(portfolio):

    result = {}

    # ==========================
    # OVERVIEW TABLE
    # ==========================

    if "Overview" in portfolio:

        df = portfolio["Overview"]

        total_value = df["Current_Value"].sum()

        top_holdings = (

            df.sort_values(
                "Current_Value",
                ascending=False
            )

        )

        result["total_value"] = total_value

        result["top_holdings"] = top_holdings


    else:

        result["total_value"] = 0

        result["top_holdings"] = pd.DataFrame()



    # ==========================
    # ASSET BREAKDOWN
    # ==========================

    if "All_Investment" in portfolio:

        asset_df = portfolio["All_Investment"]

        total_stocks = asset_df[
            asset_df["Asset"] == "Stocks"
        ]["Value"].sum()

        total_mf = asset_df[
            asset_df["Asset"] == "MFs"
        ]["Value"].sum()

        total_fd = asset_df[
            asset_df["Asset"] == "FDs"
        ]["Value"].sum()

        result["total_stocks"] = total_stocks
        result["total_mf"] = total_mf
        result["total_fd"] = total_fd

        result["asset_allocation"] = asset_df


    else:

        result["total_stocks"] = 0
        result["total_mf"] = 0
        result["total_fd"] = 0

        result["asset_allocation"] = pd.DataFrame()



    # ==========================
    # PORTFOLIO COMPOSITION
    # ==========================

    if result["total_value"] > 0:

        largest = result["top_holdings"][
            "Current_Value"
        ].max()

        largest_pct = largest / result["total_value"]

    else:

        largest_pct = 0


    result["largest_pct"] = largest_pct


    return result