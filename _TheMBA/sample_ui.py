import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk
import graphviz
from datetime import datetime

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------

st.set_page_config(
    page_title="HCP Intelligence 360",
    layout="wide"
)

# ---------------------------------------------------------
# BASE DATA
# ---------------------------------------------------------

companies = ["Apollo", "Fortis", "Max", "Narayana", "Rainbow"]
quarters = ["Q1", "Q2", "Q3", "Q4"]

# ---------------------------------------------------------
# SESSION STATE INIT
# ---------------------------------------------------------

if "selected_companies" not in st.session_state:
    st.session_state.selected_companies = companies

if "threshold" not in st.session_state:
    st.session_state.threshold = 20


# ---------------------------------------------------------
# CACHED DATA GENERATION
# ---------------------------------------------------------

@st.cache_data
def generate_mock_data():

    df = pd.DataFrame({
        "Company": np.repeat(companies, 10),
        "Revenue": np.random.randint(100, 500, 50),
        "EBITDA": np.random.randint(10, 40, 50)
    })

    return df


df_cached = generate_mock_data()


# ---------------------------------------------------------
# SIDEBAR CONTROL PANEL
# ---------------------------------------------------------

st.sidebar.title("⚙️ Control Tower")

selected_companies = st.sidebar.multiselect(
    "Select Companies",
    companies,
    default=companies
)

selected_quarters = st.sidebar.multiselect(
    "Select Quarters",
    quarters,
    default=quarters
)

threshold = st.sidebar.slider(
    "EBITDA Threshold %",
    0,
    40,
    st.session_state.threshold
)

date_range = st.sidebar.date_input(
    "Select Date Range",
    (datetime(2023,1,1), datetime.today())
)

show_raw_data = st.sidebar.toggle(
    "Show Raw Data",
    False
)

enable_alerts = st.sidebar.toggle(
    "Enable Alerts",
    True
)

# ---------------------------------------------------------
# FORM INPUTS
# ---------------------------------------------------------

st.sidebar.markdown("### Simulation Inputs")

with st.sidebar.form("simulation_form"):

    growth_rate = st.number_input(
        "Revenue Growth %",
        0,
        50,
        12
    )

    occupancy_rate = st.slider(
        "Occupancy %",
        50,
        100,
        75
    )

    submitted = st.form_submit_button(
        "Run Simulation"
    )


# ---------------------------------------------------------
# FILE UPLOADER
# ---------------------------------------------------------

uploaded_file = st.sidebar.file_uploader(
    "Upload Dataset",
    type=["csv"]
)

if uploaded_file:

    df_uploaded = pd.read_csv(uploaded_file)

    st.sidebar.success(
        "Dataset Uploaded"
    )


# ---------------------------------------------------------
# DOWNLOAD BUTTON
# ---------------------------------------------------------

download_df = pd.DataFrame({
    "Company": companies,
    "Revenue": np.random.randint(100,500,5)
})

st.sidebar.download_button(
    "Download Sample CSV",
    download_df.to_csv(index=False),
    "sample_data.csv"
)


# ---------------------------------------------------------
# RESET BUTTON
# ---------------------------------------------------------

if st.sidebar.button("Reset Dashboard"):

    st.session_state.clear()

    st.rerun()


# ---------------------------------------------------------
# HEADER
# ---------------------------------------------------------

st.title("🏥 Macro-Healthcare Sector Intelligence 360")

st.markdown("---")


# ---------------------------------------------------------
# KPI BAR
# ---------------------------------------------------------

colA, colB, colC = st.columns(3)

colA.metric(
    "Active Companies",
    len(selected_companies)
)

colB.metric(
    "EBITDA Threshold",
    threshold
)

colC.metric(
    "Growth %",
    growth_rate
)


# ---------------------------------------------------------
# ALERT LOGIC
# ---------------------------------------------------------

if enable_alerts:

    if threshold > 30:

        st.warning(
            "High EBITDA Threshold Selected"
        )

    elif threshold < 10:

        st.info(
            "Low Threshold Active"
        )


# ---------------------------------------------------------
# EXPANDER
# ---------------------------------------------------------

with st.expander("Dashboard Metadata"):

    st.write("Companies:", selected_companies)

    st.write("Quarters:", selected_quarters)

    st.write("Date Range:", date_range)


# ---------------------------------------------------------
# TABS
# ---------------------------------------------------------

tabs = st.tabs([
    "KPIs",
    "Distribution",
    "Structure",
    "Flows",
    "Geospatial & Logic"
])


# ---------------------------------------------------------
# TAB 1 — KPIs
# ---------------------------------------------------------

with tabs[0]:

    col1, col2, col3 = st.columns(3)

    with col1:

        color_logic = "#00cc96"

        if threshold > 30:
            color_logic = "red"

        fig1 = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=24.5,
            delta={'reference': threshold},
            gauge={
                'axis': {'range':[0,40]},
                'bar': {'color': color_logic}
            },
            title={'text': "Avg Margin %"}
        ))

        st.plotly_chart(fig1, use_container_width=True)


    with col2:

        categories = [
            'ARPOB',
            'Occupancy',
            'ALOS',
            'ROCE',
            'Digitalization'
        ]

        fig2 = go.Figure()

        fig2.add_trace(go.Scatterpolar(
            r=[80,90,70,85,60],
            theta=categories,
            fill='toself',
            name='Apollo'
        ))

        fig2.add_trace(go.Scatterpolar(
            r=[70,75,80,65,90],
            theta=categories,
            fill='toself',
            name='Max'
        ))

        st.plotly_chart(fig2, use_container_width=True)


    with col3:

        fig3 = px.funnel(
            pd.DataFrame({
                "Stage":[
                    "Visits",
                    "Inquiries",
                    "Consultations",
                    "Treatments"
                ],
                "Count":[
                    10000,
                    5000,
                    2500,
                    1200
                ]
            }),
            y='Stage',
            x='Count'
        )

        st.plotly_chart(fig3, use_container_width=True)


# ---------------------------------------------------------
# TAB 2 — DISTRIBUTION
# ---------------------------------------------------------

with tabs[1]:

    c1, c2, c3 = st.columns(3)

    df_v = pd.DataFrame({
        "Company": np.repeat(companies,20),
        "Price": np.random.randn(100)*5000+35000
    })

    with c1:

        fig4 = px.violin(
            df_v,
            y="Price",
            x="Company",
            box=True
        )

        st.plotly_chart(fig4, use_container_width=True)


    with c2:

        fig5 = px.box(
            df_v,
            x="Company",
            y="Price"
        )

        st.plotly_chart(fig5, use_container_width=True)


    with c3:

        fig6 = px.histogram(
            np.random.normal(45,15,1000),
            nbins=30
        )

        st.plotly_chart(fig6, use_container_width=True)


# ---------------------------------------------------------
# TAB 3 — STRUCTURE
# ---------------------------------------------------------

with tabs[2]:

    c1, c2, c3 = st.columns(3)

    with c1:

        fig7 = px.sunburst(
            path=[
                'Sector',
                'Sub',
                'Company'
            ],
            data_frame=pd.DataFrame({
                "Sector":["Healthcare"]*5,
                "Sub":[
                    "Pharmacy",
                    "Diagnostic",
                    "Hospital",
                    "Hospital",
                    "Hospital"
                ],
                "Company":companies,
                "Value":[30,20,25,15,10]
            }),
            values='Value'
        )

        st.plotly_chart(fig7, use_container_width=True)


    with c2:

        fig8 = px.treemap(
            names=companies,
            parents=["Total"]*5,
            values=[450,300,250,200,150]
        )

        st.plotly_chart(fig8, use_container_width=True)


    with c3:

        fig9 = px.pie(
            values=[40,30,20,10],
            names=[
                'Insurance',
                'Cash',
                'Government',
                'Corporate'
            ]
        )

        st.plotly_chart(fig9, use_container_width=True)


# ---------------------------------------------------------
# TAB 4 — FLOWS
# ---------------------------------------------------------

with tabs[3]:

    c1, c2 = st.columns(2)

    with c1:

        fig10 = go.Figure(go.Waterfall(
            x=[
                "Revenue",
                "Consumables",
                "Doctors",
                "Admin",
                "EBITDA"
            ],
            y=[
                100,
                -20,
                -30,
                -15,
                0
            ],
            measure=[
                "relative",
                "relative",
                "relative",
                "relative",
                "total"
            ]
        ))

        st.plotly_chart(fig10, use_container_width=True)


    with c2:

        fig11 = go.Figure(data=[go.Sankey(
            node=dict(
                label=[
                    "Input",
                    "Pharmacy",
                    "OPD",
                    "Profit"
                ]
            ),
            link=dict(
                source=[0,0,1],
                target=[1,2,3],
                value=[20,50,40]
            )
        )])

        st.plotly_chart(fig11, use_container_width=True)


    df_bubble = pd.DataFrame({
        "Rev":[12,15,8,18,10],
        "ROCE":[22,20,25,18,24],
        "Company":companies,
        "Size":[50,80,40,100,60]
    })

    fig12 = px.scatter(
        df_bubble,
        x="Rev",
        y="ROCE",
        size="Size",
        color="Company"
    )

    st.plotly_chart(fig12, use_container_width=True)


# ---------------------------------------------------------
# TAB 5 — GEO + LOGIC
# ---------------------------------------------------------

with tabs[4]:

    colA, colB = st.columns([2,1])

    with colA:

        map_data = pd.DataFrame({
            'lat':[19.07,28.61,12.97,13.08,22.57],
            'lon':[72.87,77.20,77.59,80.27,88.36],
            'val':[5000,8000,6000,4000,3000]
        })

        st.pydeck_chart(
            pdk.Deck(
                initial_view_state=pdk.ViewState(
                    latitude=20.59,
                    longitude=78.96,
                    zoom=4
                ),
                layers=[
                    pdk.Layer(
                        'ColumnLayer',
                        data=map_data,
                        get_position='[lon,lat]',
                        get_elevation='val',
                        radius=50000
                    )
                ]
            )
        )


    with colB:

        dot = graphviz.Digraph()

        dot.node('A','Emergency')

        dot.node('B','Triage')

        dot.node('C','ICU')

        dot.node('D','Ward')

        dot.edges(['AB','BC','BD'])

        st.graphviz_chart(dot)


    chart_data = pd.DataFrame(
        np.random.randn(20,3),
        columns=[
            'Apollo',
            'Fortis',
            'Max'
        ]
    )

    st.area_chart(chart_data)


# ---------------------------------------------------------
# RAW DATA DEBUG VIEW
# ---------------------------------------------------------

if show_raw_data:

    st.subheader("Raw Dataset")

    st.dataframe(
        df_cached,
        use_container_width=True
    )

# ---------------------------------------------------------
# REAL HOSPITAL GEO DATA (Flagship Units)
# ---------------------------------------------------------

hospital_geo_data = pd.DataFrame({

    "Hospital":[
        "Apollo Chennai",
        "Fortis Gurgaon",
        "Max Saket Delhi",
        "Narayana Bangalore",
        "Apollo Hyderabad",
        "Fortis Mumbai",
        "Max Lucknow",
        "Apollo Ahmedabad",
        "Narayana Kolkata"
    ],

    "City":[
        "Chennai",
        "Gurgaon",
        "Delhi",
        "Bangalore",
        "Hyderabad",
        "Mumbai",
        "Lucknow",
        "Ahmedabad",
        "Kolkata"
    ],

    "lat":[
        13.0622,
        28.4595,
        28.5244,
        12.9063,
        17.4239,
        19.0760,
        26.8467,
        23.0225,
        22.5726
    ],

    "lon":[
        80.2496,
        77.0266,
        77.2066,
        77.5857,
        78.4483,
        72.8777,
        80.9462,
        72.5714,
        88.3639
    ],

    # Performance proxy (dummy but realistic scale)
    "beds":[
        650,
        1000,
        550,
        1400,
        500,
        450,
        350,
        300,
        900
    ],

    "revenue_index":[
        95,
        110,
        90,
        130,
        85,
        80,
        70,
        65,
        105
    ]
})# ---------------------------------------------------------
# ADVANCED GEO ANALYTICS MAP
# ---------------------------------------------------------

st.subheader("National Hospital Performance Footprint")

layer = pdk.Layer(
    "ColumnLayer",
    data=hospital_geo_data,
    get_position='[lon, lat]',
    get_elevation='beds',
    elevation_scale=50,
    radius=40000,
    get_fill_color="[revenue_index, 140, 200, 180]",
    pickable=True,
    auto_highlight=True
)

view_state = pdk.ViewState(
    latitude=22.5937,
    longitude=78.9629,
    zoom=4.5,
    pitch=45
)

tooltip = {
    "html": """
        <b>Hospital:</b> {Hospital} <br/>
        <b>City:</b> {City} <br/>
        <b>Beds:</b> {beds} <br/>
        <b>Revenue Index:</b> {revenue_index}
    """,
    "style": {
        "backgroundColor": "steelblue",
        "color": "white"
    }
}

st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip
    )
)
# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.sidebar.info(
    f"Last Compiled: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)

st.sidebar.success(
    "Deployment Active"
)


st.markdown("### Executive Intelligence Panel")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Sector Growth Outlook",
    "Strong",
    "+2 Signals"
)

col2.metric(
    "System Risk Level",
    "Moderate",
    "↑ Monitoring"
)

col3.metric(
    "Valuation Signal",
    "Neutral",
    "±0%"
)

col4.metric(
    "Coverage Status",
    "5 Companies",
    "Active"
)

st.markdown("---")


st.markdown("## Sector Intelligence Summary")

st.info("""
Indian hospital chains continue to demonstrate stable occupancy growth
driven by insurance penetration and urban demand expansion.

Key Observations:

• Occupancy trends remain stable across Tier-1 markets  
• Capex expansion indicates long-term growth confidence  
• Debt levels require monitoring in aggressive expansion models  

Investment Lens:

Sector fundamentals remain structurally strong,
but valuation discipline remains critical.
""")


st.markdown("## Risk Intelligence Overview")

risk_data = pd.DataFrame({
    "Risk": [
        "Debt Expansion",
        "Doctor Cost Inflation",
        "Insurance Dependency",
        "Regulatory Pricing Risk"
    ],
    "Severity": [
        "Medium",
        "High",
        "Medium",
        "Low"
    ]
})

st.dataframe(risk_data, use_container_width=True)

st.markdown("## Valuation Commentary")

st.warning("""
DCF sensitivity indicates that valuation remains highly
sensitive to WACC assumptions.

Key Drivers:

• Revenue growth stability  
• EBITDA margin expansion  
• Capex efficiency  

Current View:

Intrinsic value remains within fair value band
under base-case assumptions.
""")

st.markdown("## System Status")

status_col1, status_col2, status_col3 = st.columns(3)

status_col1.success("Data Pipeline Active")

status_col2.info("LLM Risk Engine Ready")

status_col3.success("Dashboard Synced")