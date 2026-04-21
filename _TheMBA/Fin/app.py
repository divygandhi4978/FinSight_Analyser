import pandas as pd
import numpy as np

from datetime import datetime, timedelta
import streamlit as st

from data_loader import initialize_portfolio_data
from cleaner import clean_portfolio
from returns_engine import run_returns_engine

import os



# =====================================
# SAVE ALL DATAFRAMES AS CSV
# =====================================

def save_all_to_csv(system, base_path="output_csv"):

    os.makedirs(base_path, exist_ok=True)

    def save_dict(data, prefix=""):

        if isinstance(data, dict):

            for key, value in data.items():

                new_prefix = (
                    f"{prefix}_{key}"
                    if prefix else key
                )

                save_dict(value, new_prefix)

        elif isinstance(data, pd.DataFrame):

            filename = f"{prefix}.csv"

            filepath = os.path.join(
                base_path,
                filename
            )

            try:

                data.to_csv(
                    filepath,
                    index=False
                )

                print(
                    f"Saved: {filepath}"
                )

            except Exception as e:

                print(
                    f"Failed saving {prefix}: {e}"
                )

    save_dict(system)



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
# FAKE HISTORY (fallback safety)
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
# BUILD SYSTEM CORE
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

    returns_data = run_returns_engine(
        portfolio
    )

    return {

        "portfolio": portfolio,
        "returns": returns_data

    }



# =====================================
# IMPORT UI + ENGINES
# =====================================

from ui.home import render_home
from ui.performance import render_performance
from engine.mf_engine import run_mf_engine
from ui.mf import render_mf_page
from engine.stocks_engine import run_stock_engine
from ui.stocks import render_stock_page
from engine.fd_engine import run_fd_engine
from ui.fd import render_fd_page
from engine.research_engine import run_research_engine
from ui.research import render_research_page
from engine.performance import run_performance_engine



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
    ttl=600   # auto-refresh every 10 min
)

def load_full_system():

    system = build_system()

    # Ensure history

    if "history_daily" not in system["portfolio"]:

        system["portfolio"]["history_daily"] = (
            generate_fake_history()
        )

    if len(system["portfolio"]["history_daily"]) < 5:

        system["portfolio"]["history_daily"] = (
            generate_fake_history()
        )



    # Run engines

    system["performance"] = run_performance_engine(
        system["portfolio"]
    )

    system["mf"] = run_mf_engine(
        system["portfolio"]
    )

    system["stocks"] = run_stock_engine(
        system["portfolio"]
    )

    system["fd"] = run_fd_engine(
        system["portfolio"]
    )

    system["research"] = run_research_engine(
        system["portfolio"]
    )

    return system



# =====================================
# REFRESH BUTTON (FIXED)
# =====================================

if st.sidebar.button("🔄 Refresh Latest Data"):

    st.cache_data.clear()

    if "system" in st.session_state:

        del st.session_state.system

    st.rerun()



# =====================================
# SYSTEM LOADING (FINAL FIX)
# =====================================

def get_system():

    if "system" not in st.session_state:

        loading_msg = st.info(
            "Loading portfolio data — fetching latest data. This may take up to 40 seconds."
        )

        with st.spinner(
            "Fetching financial data — please wait..."
        ):

            st.session_state.system = load_full_system()

        loading_msg.empty()

    return st.session_state.system



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