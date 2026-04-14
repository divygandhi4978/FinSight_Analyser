import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =========================================
# CONFIG
# =========================================

BASE_SHEET_ID = "1lF2VJa_rdflWbBP063z5I2ZqDtT_kGe5Q4HIfPxcHqg"


# =========================================
# DATA LOADER
# =========================================

@st.cache_data
def load_tab(tab):

    url = (
        f"https://docs.google.com/spreadsheets/d/"
        f"{BASE_SHEET_ID}/gviz/tq?"
        f"tqx=out:csv&sheet={tab}"
    )

    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        return df

    except:
        return pd.DataFrame()


def detect_year_columns(df):

    return [

        col for col in df.columns
        if "FY" in str(col)

    ]


# =========================================
# SECTION INTRO BLOCK
# =========================================

def intro(text):

    st.markdown(
        f"""
        <div style="
        background:#111827;
        padding:12px;
        border-radius:8px;
        margin-bottom:12px;
        font-size:15px">

        {text}

        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================
# INDUSTRY DNA
# =========================================

def render_industry_dna():

    df = load_tab("INDUSTRY_THESIS")

    if df.empty:
        return

    st.subheader("Industry DNA — Key Facts")

    intro(
        "This defines how the sector structurally behaves — "
        "its demand stability, capital intensity, and "
        "unit economics profile."
    )

    categories = df["Category"].unique()

    for cat in categories:

        subset = df[df["Category"] == cat]

        st.markdown(f"### {cat}")

        cols = st.columns(2)

        for i, row in subset.iterrows():

            cols[i % 2].markdown(

                f"""
                **{row['Key']}**

                {row['Value']}
                """

            )


# =========================================
# DRIVERS
# =========================================

def render_drivers():

    df = load_tab("INDUSTRY_DRIVERS")

    if df.empty:
        return

    st.subheader("Business Drivers")

    intro(
        "Drivers translate operational efficiency "
        "into financial outcomes."
    )

    for _, row in df.iterrows():

        with st.container():

            st.markdown(

                f"""
                ### {row.iloc[0]}

                **What it means**

                {row.iloc[1]}

                **Why it matters**

                {row.iloc[2]}
                """

            )


# =========================================
# KPI SNAPSHOT
# =========================================

def render_kpi_snapshot(df):

    st.subheader("Operational Snapshot")

    years = detect_year_columns(df)

    if not years:
        return

    latest = years[-1]

    metric_col = df.columns[0]

    cols = st.columns(4)

    for i in range(min(4, len(df))):

        metric = df.iloc[i][metric_col]

        value = df.iloc[i][latest]

        cols[i].metric(

            metric,
            value

        )


# =========================================
# HEATMAP
# =========================================

def render_heatmap(df):

    st.subheader("Operational Heatmap")

    intro(
        "Heatmap highlights efficiency patterns "
        "across years."
    )

    years = detect_year_columns(df)

    metric_col = df.columns[0]

    heat_df = df.set_index(metric_col)

    fig = px.imshow(

        heat_df[years],

        text_auto=True,
        aspect="auto",

        color_continuous_scale="RdYlGn"

    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="heatmap"
    )


# =========================================
# MULTI METRIC
# =========================================

def render_multi_metric(df):

    st.subheader("Multi-Metric Graph Engine")

    intro(
        "Compare KPIs together to identify trend divergence."
    )

    years = detect_year_columns(df)

    metric_col = df.columns[0]

    selected = st.multiselect(

        "Select KPIs",
        df[metric_col].unique(),
        default=df[metric_col].unique()[:2]

    )

    frames = []

    for metric in selected:

        row = df[df[metric_col] == metric]

        values = [

            row[y].values[0]
            for y in years

        ]

        temp = pd.DataFrame({

            "Year": years,
            "Value": values,
            "Metric": metric

        })

        frames.append(temp)

    combined = pd.concat(frames)

    fig = px.line(

        combined,
        x="Year",
        y="Value",
        color="Metric",
        markers=True

    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="multi"
    )


# =========================================
# CAPACITY GRAPH
# =========================================

def render_capacity():

    df = load_tab("INDUSTRY_CAPACITY_GRAPH")

    if df.empty:
        return

    st.subheader("Capacity Expansion")

    intro(
        "Capacity growth drives long-term revenue potential."
    )

    fig = px.bar(

        df,
        x="Year",
        y="Total_Beds",
        color="Total_Beds"

    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="capacity"
    )


# =========================================
# DEMAND GRAPH
# =========================================

def render_demand():

    df = load_tab("INDUSTRY_DEMAND_GRAPH")

    if df.empty:
        return

    st.subheader("Demand Growth")

    intro(
        "Demand growth determines occupancy sustainability."
    )

    fig = go.Figure()

    fig.add_trace(go.Scatter(

        x=df["Year"],
        y=df["Outpatient_Growth_%"],
        name="Outpatient",
        mode="lines+markers"

    ))

    fig.add_trace(go.Scatter(

        x=df["Year"],
        y=df["Inpatient_Growth_%"],
        name="Inpatient",
        mode="lines+markers"

    ))

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="demand"
    )


# =========================================
# RISKS
# =========================================

def render_risks():

    df = load_tab("INDUSTRY_RISKS")

    if df.empty:
        return

    st.subheader("Risk Radar")

    intro(
        "Risks define downside and margin volatility."
    )

    cols = st.columns(3)

    for i, row in df.iterrows():

        cols[i % 3].error(

            f"""
            **{row.iloc[0]}**

            {row.iloc[1]}
            """

        )


# =========================================
# GLOSSARY (FIXED)
# =========================================

def render_glossary():

    df = load_tab("INDUSTRY_GLOSSARY")

    if df.empty:
        return

    st.subheader("Glossary")

    intro(
        "Reference definitions used across sector analysis."
    )

    search = st.text_input("Search term")

    if search:

        df = df[

            df.iloc[:,0]
            .astype(str)
            .str.contains(search, case=False)

        ]

    st.dataframe(df)


# =========================================
# MASTER FLOW
# =========================================

def show_industry_overview():

    st.title(
        "Healthcare Industry Intelligence"
    )

    render_industry_dna()

    render_drivers()

    op_df = load_tab("INDUSTRY_OPERATIONS")

    render_kpi_snapshot(op_df)

    render_heatmap(op_df)

    render_multi_metric(op_df)

    render_capacity()

    render_demand()

    render_risks()

    render_glossary()