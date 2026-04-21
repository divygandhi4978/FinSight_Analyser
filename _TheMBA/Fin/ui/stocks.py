import streamlit as st
import plotly.express as px
import pandas as pd



def render_stock_page(system):

    st.title("Stock Analytics")

    stock_data = system.get("stocks", {})

    if not stock_data:

        st.warning("No stock data available")

        return


    alloc = stock_data.get("allocation")

    stock_dict = stock_data.get("stock_data")


    if alloc is None or stock_dict is None:

        st.warning("Stock dataset incomplete")

        return


    # =====================================
    # TOP PORTFOLIO KPIs
    # =====================================

    total_value = 0
    num_stocks = 0
    largest_stock = "NA"

    avg_pe = None
    avg_beta = None


    # =====================================
    # GET TRUE STOCK VALUE
    # FROM All_Investment TABLE
    # =====================================

    portfolio = system.get("portfolio", {})

    asset_table = None

    for key in portfolio:

        if "investment" in key.lower():

            asset_table = portfolio[key]

            break


    if asset_table is not None:

        try:

            stock_row = asset_table[

                asset_table["Asset"]

                .astype(str)

                .str.lower()

                .str.contains("stock")

            ]

            if not stock_row.empty:

                total_value = stock_row["Value"].iloc[0]

        except:

            total_value = 0


    # =====================================
    # FALLBACK (if asset table missing)
    # =====================================

    if total_value == 0:

        if "Current_Value" in alloc.columns:

            total_value = alloc["Current_Value"].sum()


    # =====================================
    # OTHER METRICS
    # =====================================

    if "Current_Value" in alloc.columns:

        num_stocks = len(alloc)

        try:

            largest_row = alloc.loc[
                alloc["Current_Value"].idxmax()
            ]

            largest_stock = largest_row.get(
                "Company_Name",
                "NA"
            )

        except:

            largest_stock = "NA"


    pe_values = []
    beta_values = []


    for s in stock_dict:

        fundamentals = stock_dict[s].get(
            "fundamentals",
            {}
        )

        pe = fundamentals.get("trailingPE")
        beta = fundamentals.get("beta")

        if pe is not None:

            pe_values.append(pe)

        if beta is not None:

            beta_values.append(beta)


    if len(pe_values) > 0:

        avg_pe = sum(pe_values) / len(pe_values)

    if len(beta_values) > 0:

        avg_beta = sum(beta_values) / len(beta_values)


    # =====================================
    # KPI DISPLAY
    # =====================================

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric(
        "Total Stock Value",
        f"₹{total_value:,.0f}"
    )

    k2.metric(
        "Number of Stocks",
        num_stocks
    )

    k3.metric(
        "Largest Holding",
        largest_stock
    )

    k4.metric(
        "Average PE",
        f"{avg_pe:.2f}"
        if avg_pe else "NA"
    )

    k5.metric(
        "Portfolio Beta",
        f"{avg_beta:.2f}"
        if avg_beta else "NA"
    )


    st.divider()


    # =====================================
    # ALLOCATION VISUALS
    # =====================================

    if "Current_Value" in alloc.columns:

        col1, col2 = st.columns(2)


        fig_pie = px.pie(
            alloc,
            values="Current_Value",
            names="Company_Name",
            hole=0.5
        )

        col1.subheader("Stock Allocation")

        col1.plotly_chart(
            fig_pie,
            width="stretch"
        )


        sorted_df = alloc.sort_values(
            "Current_Value",
            ascending=True
        )


        fig_bar = px.bar(
            sorted_df,
            x="Current_Value",
            y="Company_Name",
            orientation="h"
        )

        fig_bar.update_layout(
            yaxis=dict(
                autorange="reversed"
            )
        )

        col2.subheader("Stock Ranking")

        col2.plotly_chart(
            fig_bar,
            width="stretch"
        )


    st.divider()


    # =====================================
    # STOCK SELECTOR
    # =====================================

    stock_list = list(stock_dict.keys())

    selected_stock = st.selectbox(
        "Select Stock",
        stock_list
    )


    data = stock_dict[selected_stock]

    df = data.get("history")

    fundamentals = data.get(
        "fundamentals",
        {}
    )


    st.divider()


    # =====================================
    # PRICE TREND
    # =====================================

    if df is not None:

        st.subheader("Price Trend")

        st.plotly_chart(
            px.line(
                df,
                x="Date",
                y="Close"
            ),
            width="stretch"
        )


    st.divider()


    # =====================================
    # RAW FUNDAMENTALS
    # =====================================

    st.subheader("Detailed Fundamentals")

    fund_df = pd.DataFrame(
        fundamentals.items(),
        columns=["Metric", "Value"]
    )

    st.dataframe(
        fund_df,
        width="stretch"
    )