import streamlit as st
import pandas as pd
import plotly.express as px


# =====================================
# HELPER FUNCTIONS
# =====================================

def find_table_key(portfolio: dict, keywords: list) -> str:
    """Finds the first key in the portfolio that contains any of the keywords."""
    for key in portfolio.keys():
        lower = str(key).lower()
        if any(word in lower for word in keywords):
            return key
    return None


# =====================================
# UI COMPONENT FUNCTIONS
# =====================================

def render_kpis(portfolio: dict):
    """Renders the top-level KPI metrics."""
    col1, col2, col3, col4 = st.columns(4)

    total_value, stocks_val, mf_val, fd_val = 0, 0, 0, 0

    if "Overview" in portfolio and not portfolio["Overview"].empty:
        df = portfolio["Overview"]
        if "Current_Value" in df.columns:
            total_value = df["Current_Value"].sum()

    if "All_Investment" in portfolio and not portfolio["All_Investment"].empty:
        asset_df = portfolio["All_Investment"]
        if "Asset" in asset_df.columns and "Value" in asset_df.columns:
            stocks_val = asset_df[asset_df["Asset"] == "Stocks"]["Value"].sum()
            mf_val = asset_df[asset_df["Asset"] == "MFs"]["Value"].sum()
            fd_val = asset_df[asset_df["Asset"] == "FDs"]["Value"].sum()

    col1.metric("Total Value", f"₹{total_value:,.0f}")
    col2.metric("Total Stocks", f"₹{stocks_val:,.0f}")
    col3.metric("Total MFs", f"₹{mf_val:,.0f}")
    col4.metric("Total FD", f"₹{fd_val:,.0f}")
    st.divider()


def render_asset_allocation(portfolio: dict, col):
    """Renders the Asset Allocation Pie Chart."""
    if "All_Investment" in portfolio and not portfolio["All_Investment"].empty:
        alloc = portfolio["All_Investment"]
        if "Value" in alloc.columns and "Asset" in alloc.columns:
            col.subheader("Asset Allocation")
            fig_pie = px.pie(alloc, values="Value", names="Asset", hole=0.5)
            col.plotly_chart(fig_pie, use_container_width=True)


def render_top_holdings(portfolio: dict, col):
    """Renders the Top Holdings Bar Chart dynamically based on rows available."""
    if "Overview" in portfolio and not portfolio["Overview"].empty:
        df = portfolio["Overview"]
        
        # Ensure necessary columns exist
        if "Current_Value" in df.columns and "Company_Name" in df.columns:
            df_sorted = df.sort_values("Current_Value", ascending=False)
            max_limit = len(df_sorted)
            
            # Prevent slider from breaking if there's only 1 row
            default_val = min(10, max_limit)
            min_val = min(5, max_limit)
            
            max_rows = st.slider("Number of Holdings", min_value=min_val, max_value=max_limit, value=default_val)
            
            df_display = df_sorted.head(max_rows)
            fig_bar = px.bar(df_display, x="Current_Value", y="Company_Name", orientation="h")
            fig_bar.update_layout(yaxis=dict(autorange="reversed"))
            
            col.subheader("Top Holdings")
            col.plotly_chart(fig_bar, use_container_width=True)


def render_portfolio_growth(portfolio: dict):
    """Renders the Portfolio Growth Line Chart over time."""
    if "history_daily" in portfolio and not portfolio["history_daily"].empty:
        hist = portfolio["history_daily"]
        if "Date" in hist.columns and "Total_Value" in hist.columns:
            st.subheader("Portfolio Growth")
            fig_line = px.line(hist, x="Date", y="Total_Value")
            st.plotly_chart(fig_line, use_container_width=True)


def render_mf_distribution(portfolio: dict):
    """Renders the Mutual Fund Distribution Analytics."""
    mf_key = find_table_key(portfolio, ["mf", "fund"])
    
    if mf_key and not portfolio[mf_key].empty:
        mf_df = portfolio[mf_key].copy()
        
        if "Value" in mf_df.columns:
            st.divider()
            st.subheader("Mutual Fund Distribution")

            # Create a dynamic unique label using the first column + index
            first_col = mf_df.columns[0]
            mf_df["MF_Label"] = mf_df[first_col].astype(str) + " (" + mf_df.index.astype(str) + ")"

            col_mf1, col_mf2 = st.columns(2)

            fig_mf_pie = px.pie(mf_df, values="Value", names="MF_Label", hole=0.5)
            col_mf1.plotly_chart(fig_mf_pie, use_container_width=True)

            fig_mf_bar = px.bar(mf_df, x="Value", y="MF_Label", orientation="h")
            fig_mf_bar.update_layout(yaxis=dict(autorange="reversed"))
            col_mf2.plotly_chart(fig_mf_bar, use_container_width=True)

            with st.expander("View MF Details", expanded=False):
                st.dataframe(mf_df.drop(columns=["MF_Label"]), use_container_width=True)

def render_fd_analytics(portfolio: dict):
    """Renders Fixed Deposit Analytics with corrected visuals and logic."""

    fd_key = find_table_key(
        portfolio,
        ["fd", "fixed deposit"]
    )

    if fd_key and not portfolio[fd_key].empty:

        fd_df = portfolio[fd_key].copy()

        st.divider()
        st.subheader("Fixed Deposit Analytics")


        # =====================================
        # CLEAN LABELS
        # =====================================

        if (
            "Bank_Post_Office" in fd_df.columns
            and "Holder_Name" in fd_df.columns
            and "FD_ID" in fd_df.columns
        ):

            fd_df["FD_Label"] = (

                fd_df["Bank_Post_Office"]

                .astype(str)

                .str.split()

                .str[0]

                + " | "

                + fd_df["Holder_Name"]

                .astype(str)

                + " | "

                + fd_df["FD_ID"]

                .astype(str)

                .str[-4:]

            )

        elif "FD_ID" in fd_df.columns:

            fd_df["FD_Label"] = (

                "FD "

                + fd_df["FD_ID"]

                .astype(str)

                .str[-4:]

            )

        else:

            fd_df["FD_Label"] = (

                "FD_"

                + fd_df.index.astype(str)

            )


        # =====================================
        # VALUE COLUMN DETECTION
        # =====================================

        value_col = None

        for col in [

            "Principal_Amount",

            "Amount",

            "Value",

            "Current_Value"

        ]:

            if col in fd_df.columns:

                value_col = col
                break


        # =====================================
        # VALUE DISTRIBUTION
        # =====================================

        if value_col:

            col_fd1, col_fd2 = st.columns(2)

            fig_fd_pie = px.pie(

                fd_df,

                values=value_col,

                names="FD_Label",

                hole=0.5

            )

            col_fd1.markdown(
                "**FD Allocation by Value**"
            )

            col_fd1.plotly_chart(
                fig_fd_pie,
                use_container_width=True
            )


            # SORTED RANKING

            sorted_df = fd_df.sort_values(
                value_col,
                ascending=True
            )

            fig_fd_bar_value = px.bar(

                sorted_df,

                x=value_col,

                y="FD_Label",

                orientation="h"

            )

            fig_fd_bar_value.update_layout(
                yaxis=dict(autorange="reversed")
            )

            col_fd2.markdown(
                "**FD Value Ranking**"
            )

            col_fd2.plotly_chart(
                fig_fd_bar_value,
                use_container_width=True
            )


        # =====================================
        # DAYS TO MATURITY
        # =====================================

        if "Maturity_Date" in fd_df.columns:

            fd_df["Maturity_Date"] = pd.to_datetime(

                fd_df["Maturity_Date"],

                errors="coerce"

            )

            today = pd.Timestamp.today()

            fd_df["Days_to_Maturity"] = (

                fd_df["Maturity_Date"]

                - today

            ).dt.days


        # =====================================
        # MATURITY LADDER
        # =====================================

        if "Days_to_Maturity" in fd_df.columns:

            ladder_df = fd_df.dropna(

                subset=["Days_to_Maturity"]

            )

            if not ladder_df.empty:

                st.markdown(
                    "**FD Maturity Ladder**"
                )

                fig_maturity = px.scatter(

                    ladder_df,

                    x="Days_to_Maturity",

                    y="FD_Label",

                    size=value_col,

                    color=value_col,

                    orientation="h"

                )

                st.plotly_chart(
                    fig_maturity,
                    use_container_width=True
                )


        # =====================================
        # TIMELINE
        # =====================================

        if (

            "Investment_Date" in fd_df.columns

            and "Maturity_Date" in fd_df.columns

        ):

            fd_df["Investment_Date"] = pd.to_datetime(

                fd_df["Investment_Date"],

                errors="coerce"

            )

            fd_df["Maturity_Date"] = pd.to_datetime(

                fd_df["Maturity_Date"],

                errors="coerce"

            )

            timeline_df = fd_df.dropna(

                subset=[

                    "Investment_Date",

                    "Maturity_Date"

                ]

            )

            if not timeline_df.empty:

                st.markdown(
                    "**FD Lifecycle Timeline**"
                )

                fig_timeline = px.timeline(

                    timeline_df,

                    x_start="Investment_Date",

                    x_end="Maturity_Date",

                    y="FD_Label",

                    color=value_col

                )

                fig_timeline.update_yaxes(
                    autorange="reversed"
                )

                st.plotly_chart(
                    fig_timeline,
                    use_container_width=True
                )


        # =====================================
        # TABLE
        # =====================================

        with st.expander(

            "View FD Details",

            expanded=False

        ):

            st.dataframe(

                fd_df.drop(

                    columns=["FD_Label"]

                ),

                use_container_width=True

            )

# =====================================
# MAIN RENDER ENTRY POINT
# =====================================

def render_home(system: dict):
    """Main rendering function for the home page."""
    portfolio = system.get("portfolio", {})

    st.title("FinSight : Portfolio Analytics")
    st.divider()

    # Avoid rendering if portfolio is entirely empty
    if not portfolio:
        st.info("No portfolio data found. Please load your data to view analytics.")
        return

    # Render Sections Modularly
    render_kpis(portfolio)
    
    col_left, col_right = st.columns(2)
    render_asset_allocation(portfolio, col_left)
    render_top_holdings(portfolio, col_right)
    
    render_portfolio_growth(portfolio)
    render_mf_distribution(portfolio)
    render_fd_analytics(portfolio)