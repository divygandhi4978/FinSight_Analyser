import streamlit as st
import altair as alt
import pandas as pd

# FIX — import cached loader, NOT build_system
from app import get_system


# ==========================
# PAGE CONFIG
# ==========================

st.set_page_config(
    page_title="Alpha Terminal",
    page_icon="📟",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==========================
# PREMIUM DARK THEME
# ==========================

st.markdown("""
<style>

/* Main Background */

.main {
    background-color: #050505;
}

/* Metric Cards */

[data-testid="metric-container"] {
    background-color: #0E1117;
    border: 1px solid #1E293B;
    padding: 20px;
    border-radius: 4px;
}

/* Sidebar */

section[data-testid="stSidebar"] {
    background-color: #0E1117;
}

/* Scrollbar */

::-webkit-scrollbar {
    width: 5px;
}

::-webkit-scrollbar-track {
    background: #050505;
}

::-webkit-scrollbar-thumb {
    background: #1E293B;
}

</style>
""", unsafe_allow_html=True)


# ==========================
# LOAD SYSTEM (CACHED)
# ==========================

system = get_system()

portfolio = system.get("portfolio", {})
returns = system.get("returns", {})
allocations = system.get("allocations", {})


# ==========================
# SIDEBAR TERMINAL
# ==========================

with st.sidebar:

    st.markdown(
        "<h2 style='color: #10B981;'>[ ALPHA_v2.0 ]</h2>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.code(
        "STATUS: ENGINES_ONLINE\nREGION: LOCAL\nUSER: ROOT",
        language="bash"
    )

    st.markdown("---")

    if st.button("> REBOOT_SYSTEM", use_container_width=True):

        st.cache_data.clear()

        if "system" in st.session_state:

            del st.session_state["system"]

        st.rerun()


# ==========================
# KPI SECTION
# ==========================

growth_df = returns.get("growth_curve")

cagr = returns.get("CAGR")

if growth_df is not None and not growth_df.empty:

    current_val = growth_df[
        "Total_Value"
    ].iloc[-1]

else:

    current_val = 0


# SAFE allocation read

stock_alloc = allocations.get(
    "stock_allocation"
)

positions = (

    len(stock_alloc)

    if isinstance(
        stock_alloc,
        pd.DataFrame
    )

    else 0

)


m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "Equity_Total",
    f"₹{current_val:,.0f}"
)

m2.metric(
    "CAGR_Alpha",
    "N/A"
    if cagr is None
    else f"{cagr*100:.2f}%"
)

m3.metric(
    "Positions",
    positions
)

m4.metric(
    "Volatility",
    "Calculated"
)

st.markdown("---")


# ==========================
# MAIN INTERFACE
# ==========================

t1, t2, t3 = st.tabs([

    "01_PERFORMANCE",

    "02_ALLOCATION",

    "03_RAW_LOGS"

])


# ==========================
# PERFORMANCE TAB
# ==========================

with t1:

    growth = returns.get(
        "growth_curve"
    )

    if growth is not None:

        chart = alt.Chart(growth).mark_area().encode(

            x="Date:T",

            y="Total_Value:Q",

            tooltip=[
                "Date:T",
                "Total_Value:Q"
            ]

        ).properties(height=450)

        st.altair_chart(
            chart,
            use_container_width=True
        )


# ==========================
# ALLOCATION TAB
# ==========================

with t2:

    seg = allocations.get(
        "segment_allocation"
    )

    stock = allocations.get(
        "stock_allocation"
    )

    c1, c2 = st.columns(2)


    # Segment Pie

    with c1:

        if seg is not None:

            pie = alt.Chart(seg).mark_arc().encode(

                theta="Segment_%:Q",

                color="Segment:N",

                tooltip=[
                    "Segment",
                    "Segment_%"
                ]

            )

            st.altair_chart(
                pie,
                use_container_width=True
            )


    # Stock Bars

    with c2:

        if stock is not None:

            bar = alt.Chart(

                stock.head(10)

            ).mark_bar().encode(

                x="Stock_%:Q",

                y=alt.Y(
                    "Company_Name:N",
                    sort="-x"
                )

            )

            st.altair_chart(
                bar,
                use_container_width=True
            )


# ==========================
# RAW DATA TAB
# ==========================

with t3:

    for key, df in portfolio.items():

        if isinstance(
            df,
            pd.DataFrame
        ):

            if not df.empty:

                st.markdown(
                    f"**LOG_ENTRY: {key.upper()}**"
                )

                st.dataframe(
                    df,
                    use_container_width=True
                )