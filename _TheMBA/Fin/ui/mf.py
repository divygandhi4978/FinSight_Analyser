import streamlit as st
import plotly.express as px
import pandas as pd



def render_mf_page(system):

    st.title("Mutual Fund Analytics")

    mf_data = system.get("mf", {})

    if not mf_data:

        st.warning("No MF data available")

        return


    alloc = mf_data.get("allocation")

    nav_dict = mf_data.get("fund_nav")


    if alloc is None or nav_dict is None:

        st.warning("MF dataset incomplete")

        return


    # =====================================
    # GET TRUE MF VALUE FROM MASTER TABLE
    # =====================================

    total_value = 0

    portfolio = system.get("portfolio", {})

    asset_table = None

    for key in portfolio:

        if "investment" in key.lower():

            asset_table = portfolio[key]

            break


    if asset_table is not None:

        try:

            mf_row = asset_table[

                asset_table["Asset"]

                .astype(str)

                .str.lower()

                .str.contains("mf")

            ]

            if not mf_row.empty:

                total_value = mf_row["Value"].iloc[0]

        except:

            total_value = 0


    # =====================================
    # FALLBACK LOGIC
    # =====================================

    if total_value == 0:

        if "Value" in alloc.columns:

            total_value = alloc["Value"].sum()


    # =====================================
    # TOP MF PORTFOLIO KPIs
    # =====================================

    num_funds = len(alloc)

    largest_fund = "NA"

    avg_return = None

    avg_drawdown = None


    try:

        largest_row = alloc.loc[
            alloc["Value"].idxmax()
        ]

        largest_fund = largest_row.iloc[0]

    except:

        largest_fund = "NA"


    return_vals = []

    dd_vals = []


    for fund in nav_dict:

        df = nav_dict[fund]

        if "Return" in df.columns:

            r = df["Return"].mean()

            if pd.notna(r):

                return_vals.append(r)


        if "Drawdown" in df.columns:

            d = df["Drawdown"].min()

            if pd.notna(d):

                dd_vals.append(d)


    if len(return_vals) > 0:

        avg_return = sum(return_vals) / len(return_vals)


    if len(dd_vals) > 0:

        avg_drawdown = sum(dd_vals) / len(dd_vals)


    # =====================================
    # KPI DISPLAY
    # =====================================

    k1, k2, k3, k4, k5 = st.columns(5)

    k1.metric(
        "Total MF Value",
        f"₹{total_value:,.0f}"
    )

    k2.metric(
        "Number of Funds",
        num_funds
    )

    k3.metric(
        "Largest Fund",
        largest_fund
    )

    k4.metric(
        "Avg Daily Return",
        f"{avg_return:.4%}"
        if avg_return else "NA"
    )

    k5.metric(
        "Worst Drawdown",
        f"{avg_drawdown:.2%}"
        if avg_drawdown else "NA"
    )


    st.divider()


    # =====================================
    # ALLOCATION VISUALS
    # =====================================

    if "Value" in alloc.columns:

        col1, col2 = st.columns(2)


        fig_pie = px.pie(
            alloc,
            values="Value",
            names=alloc.columns[0],
            hole=0.5
        )

        col1.subheader("MF Allocation")

        col1.plotly_chart(
            fig_pie,
            width="stretch"
        )


        sorted_df = alloc.sort_values(
            "Value",
            ascending=True
        )


        fig_bar = px.bar(
            sorted_df,
            x="Value",
            y=alloc.columns[0],
            orientation="h"
        )

        fig_bar.update_layout(
            yaxis=dict(
                autorange="reversed"
            )
        )


        col2.subheader("Fund Ranking")

        col2.plotly_chart(
            fig_bar,
            width="stretch"
        )


    st.divider()


    # =====================================
    # FUND SELECTOR
    # =====================================

    fund_list = list(nav_dict.keys())

    selected_fund = st.selectbox(
        "Select Fund",
        fund_list
    )


    df = nav_dict[selected_fund]


    st.divider()


    # =====================================
    # NAV TREND
    # =====================================

    st.subheader("NAV Trend")

    st.plotly_chart(
        px.line(
            df,
            x="date",
            y="nav"
        ),
        width="stretch"
    )


    # =====================================
    # RETURNS
    # =====================================

    if "Return" in df.columns:

        st.subheader("Daily Returns")

        st.plotly_chart(
            px.line(
                df,
                x="date",
                y="Return"
            ),
            width="stretch"
        )


        st.subheader("Return Distribution")

        st.plotly_chart(
            px.histogram(
                df,
                x="Return",
                nbins=50
            ),
            width="stretch"
        )


    # =====================================
    # ROLLING RETURNS
    # =====================================

    roll_cols = [

        c for c in df.columns

        if "Rolling_" in c

    ]


    if roll_cols:

        st.subheader("Rolling Returns")

        st.plotly_chart(
            px.line(
                df,
                x="date",
                y=roll_cols
            ),
            width="stretch"
        )


    # =====================================
    # DRAWDOWN
    # =====================================

    if "Drawdown" in df.columns:

        st.subheader("Drawdown Curve")

        st.plotly_chart(
            px.line(
                df,
                x="date",
                y="Drawdown"
            ),
            width="stretch"
        )


    st.divider()


    # =====================================
    # RAW DATA TABLE
    # =====================================

    st.subheader("Fund Data")

    st.dataframe(
        df.tail(50),
        width="stretch"
    )