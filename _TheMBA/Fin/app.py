import pandas as pd
import numpy as np

from datetime import datetime, timedelta
import streamlit as st

from data_loader import initialize_portfolio_data
from cleaner import clean_portfolio
from returns_engine import run_returns_engine

# IMPORTANT — restore this
from allocation import run_allocation_engine



# =====================================
# REPAIR DATAFRAME
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

    df = df.loc[
        :,
        ~df.columns.duplicated()
    ]

    return df



# =====================================
# SAFE HISTORY GENERATOR
# =====================================

def generate_fake_history():

    rows = []

    start = datetime(2026, 1, 1)

    value = 1000000

    for i in range(180):

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
# BUILD SYSTEM CORE (FIXED)
# =====================================

def build_system():

    raw = initialize_portfolio_data()

    portfolio = clean_portfolio(raw)

    for k in portfolio:

        if isinstance(
            portfolio[k],
            pd.DataFrame
        ):

            portfolio[k] = repair_dataframe(
                portfolio[k]
            )



    # RETURNS
    returns_data = run_returns_engine(
        portfolio
    )



    # ALLOCATIONS — FIXED
    try:

        allocation_data = run_allocation_engine(
            portfolio
        )

    except Exception as e:

        print(
            "Allocation engine failed:",
            e
        )

        allocation_data = {}



    return {

        "portfolio": portfolio,

        "returns": returns_data,

        "allocations": allocation_data

    }



# =====================================
# IMPORT UI + ENGINES
# =====================================

from ui.home import render_home
from ui.performance import render_performance

from engine.performance import run_performance_engine
from engine.mf_engine import run_mf_engine
from engine.stocks_engine import run_stock_engine
from engine.fd_engine import run_fd_engine
from engine.research_engine import run_research_engine

from ui.mf import render_mf_page
from ui.stocks import render_stock_page
from ui.fd import render_fd_page
from ui.research import render_research_page



# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(

    page_title="FinSight : Portfolio Analytics",

    layout="wide"

)



# =====================================
# CACHE SYSTEM LOAD
# =====================================

@st.cache_data(
    show_spinner=True,
    ttl=600
)

def load_full_system():

    system = build_system()

    portfolio = system.get(
        "portfolio",
        {}
    )



    # Ensure history exists

    if "history_daily" not in portfolio:

        portfolio[
            "history_daily"
        ] = generate_fake_history()



    if len(
        portfolio["history_daily"]
    ) < 10:

        portfolio[
            "history_daily"
        ] = generate_fake_history()



    # Run Engines Safely

    try:

        system["performance"] = (
            run_performance_engine(
                portfolio
            )
        )

    except Exception as e:

        print(
            "Performance engine failed:",
            e
        )

        system["performance"] = {}



    try:

        system["mf"] = (
            run_mf_engine(
                portfolio
            )
        )

    except Exception as e:

        print(
            "MF engine failed:",
            e
        )

        system["mf"] = {}



    try:

        system["stocks"] = (
            run_stock_engine(
                portfolio
            )
        )

    except Exception as e:

        print(
            "Stock engine failed:",
            e
        )

        system["stocks"] = {}



    try:

        system["fd"] = (
            run_fd_engine(
                portfolio
            )
        )

    except Exception as e:

        print(
            "FD engine failed:",
            e
        )

        system["fd"] = {}



    try:

        system["research"] = (
            run_research_engine(
                portfolio
            )
        )

    except Exception as e:

        print(
            "Research engine failed:",
            e
        )

        system["research"] = {}



    return system



# =====================================
# REFRESH BUTTON
# =====================================

if st.sidebar.button("🔄 Refresh Latest Data"):

    st.cache_data.clear()

    if "system" in st.session_state:

        del st.session_state.system

    st.rerun()



# =====================================
# SYSTEM LOAD CONTROL
# =====================================

def get_system():

    if "system" not in st.session_state:

        loading_msg = st.info(
            "Loading portfolio data — fetching latest market data. This may take up to 40 seconds."
        )

        with st.spinner(
            "Fetching financial data — please wait..."
        ):

            st.session_state[
                "system"
            ] = load_full_system()

        loading_msg.empty()

    return st.session_state["system"]



system = get_system()



# =====================================
# NAVIGATION
# =====================================

page = st.sidebar.selectbox(

    "Navigation",

    [

        "Home",

        "Performance",

        "Mutual Funds",

        "Stocks",

        "Fixed Deposits",

        "Research"

    ]

)



# =====================================
# PAGE ROUTING
# =====================================

if page == "Home":

    render_home(system)



elif page == "Performance":

    render_performance(system)



elif page == "Mutual Funds":

    render_mf_page(system)



elif page == "Stocks":

    render_stock_page(system)



elif page == "Fixed Deposits":

    render_fd_page(system)



elif page == "Research":

    render_research_page(system)