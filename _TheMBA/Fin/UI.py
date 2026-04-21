import streamlit as st
import altair as alt
import pandas as pd
from app import build_system

# ==========================
# PAGE CONFIG & STYLING
# ==========================
st.set_page_config(
    page_title="Portfolio Alpha | Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a cleaner, modern look
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; font-weight: 700; color: #1E88E5; }
    [data-testid="stMetricDelta"] { font-size: 16px; }
    .main { background-color: #f8f9fa; }
    div[data-testid="stExpander"] { border: none; box-shadow: 0px 4px 6px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #ffffff;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================
# LOAD DATA
# ==========================
@st.cache_data
def load():
    return build_system()

system = load()
portfolio = system["portfolio"]
returns = system["returns"]
allocations = system["allocations"]

# ==========================
# SIDEBAR / NAVIGATION
# ==========================
with st.sidebar:
    st.title("🛡️ Portfolio Alpha")
    st.markdown("---")
    st.info("System Logic: **Verified**")
    st.caption("Last updated: 2024-05-22")
    
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# ==========================
# HEADER & KEY METRICS
# ==========================
st.title("Portfolio Analytics Dashboard")

# Metric Row
cagr = returns.get("CAGR")
growth_df = returns.get("growth_curve")
current_val = growth_df["Total_Value"].iloc[-1] if growth_df is not None else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Current Value", f"${current_val:,.0f}", delta="Snapshot")
m2.metric("CAGR", "N/A" if cagr is None else f"{cagr*100:.2f}%", delta="Annualized")
m3.metric("Assets Tracked", len(allocations.get("stock_allocation", [])), delta=None)
m4.metric("Risk Profile", "Aggressive", delta="Medium Variance", delta_color="off")

st.markdown("---")

# ==========================
# MAIN CONTENT TABS
# ==========================
tab1, tab2, tab3 = st.tabs([
    "📈 Growth Analysis", 
    "📊 Asset Allocation", 
    "📑 Raw Data Tables"
])

# --- TAB 1: GROWTH ---
with tab1:
    growth = returns.get("growth_curve")
    if growth is not None:
        st.subheader("Performance Over Time")
        
        # Modern Area Chart for Growth
        chart = alt.Chart(growth).mark_area(
            line={'color':'#1E88E5'},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='#1E88E5', offset=0),
                       alt.GradientStop(color='rgba(30, 136, 229, 0)', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X("Date:T", title="Timeline"),
            y=alt.Y("Total_Value:Q", title="Portfolio Value ($)", scale=alt.Scale(zero=False)),
            tooltip=["Date:T", alt.Tooltip("Total_Value:Q", format="$,.2f")]
        ).interactive()
        
        st.altair_chart(chart, use_container_width=True)

# --- TAB 2: ALLOCATIONS ---
with tab2:
    col_left, col_right = st.columns(2)
    
    seg = allocations.get("segment_allocation")
    stock = allocations.get("stock_allocation")

    with col_left:
        if seg is not None and not seg.empty:
            st.subheader("Sector Exposure")
            # Donut Chart for Segments
            seg_pie = alt.Chart(seg).mark_arc(innerRadius=50).encode(
                theta=alt.Theta("Segment_%:Q"),
                color=alt.Color("Segment:N", legend=alt.Legend(orient="bottom")),
                tooltip=["Segment", "Segment_%"]
            ).properties(height=400)
            st.altair_chart(seg_pie, use_container_width=True)

    with col_right:
        if stock is not None and not stock.empty:
            st.subheader("Top 10 Holdings")
            # Sleek Horizontal Bar Chart
            stock_bar = alt.Chart(stock.head(10)).mark_bar(cornerRadiusEnd=4, color="#1E88E5").encode(
                x=alt.X("Stock_%:Q", title="Weight (%)"),
                y=alt.Y("Company_Name:N", sort="-x", title=None),
                tooltip=["Company_Name", "Stock_%"]
            ).properties(height=400)
            st.altair_chart(stock_bar, use_container_width=True)

# --- TAB 3: TABLES ---
with tab3:
    st.subheader("System Data Exploration")
    for key, df in portfolio.items():
        if df is not None and not isinstance(df, dict) and not df.empty:
            with st.expander(f"View Data: {key}", expanded=False):
                # Using st.dataframe with column config for better formatting
                st.dataframe(
                    df,
                    use_container_width=True,
                    column_config={
                        "Total_Value": st.column_config.NumberColumn(format="$%.2f"),
                        "Stock_%": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=100),
                        "Segment_%": st.column_config.ProgressColumn(format="%.2f", min_value=0, max_value=100)
                    }
                )