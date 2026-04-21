import streamlit as st
import altair as alt
import pandas as pd
from app import build_system

# ==========================
# 1. PREMIUM DARK THEME (CSS)
# ==========================
st.set_page_config(
    page_title="Alpha Terminal",
    page_icon="📟",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* Main Background and Font */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    .main {
        background-color: #050505;
        font-family: 'Inter', sans-serif;
    }

    /* Metric Card - Terminal Style */
    [data-testid="metric-container"] {
        background-color: #0E1117;
        border: 1px solid #1E293B;
        padding: 20px;
        border-radius: 4px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.5);
    }
    
    [data-testid="stMetricLabel"] {
        color: #94A3B8;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        text-transform: uppercase;
    }

    [data-testid="stMetricValue"] {
        color: #10B981 !important; /* Neon Emerald */
        font-family: 'JetBrains Mono', monospace;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #050505;
        gap: 2px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: #0E1117;
        border: 1px solid #1E293B;
        color: #64748B;
        padding: 10px 30px;
        font-family: 'JetBrains Mono', monospace;
    }

    .stTabs [aria-selected="true"] {
        background-color: #1E293B !important;
        color: #10B981 !important;
        border-bottom: 2px solid #10B981 !important;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #0E1117;
        border-right: 1px solid #1E293B;
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-track { background: #050505; }
    ::-webkit-scrollbar-thumb { background: #1E293B; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# ==========================
# 2. DATA LOAD
# ==========================
@st.cache_data(ttl=60)
def load():
    return build_system()

system = load()
portfolio, returns, allocations = system["portfolio"], system["returns"], system["allocations"]

# ==========================
# 3. SIDEBAR TERMINAL
# ==========================
with st.sidebar:
    st.markdown("<h2 style='color: #10B981; font-family: monospace;'>[ ALPHA_v2.0 ]</h2>", unsafe_allow_html=True)
    st.markdown("---")
    st.code("STATUS: ENGINES_ONLINE\nREGION: US_EAST_1\nUSER: ROOT_AUTH", language="bash")
    st.markdown("---")
    
    if st.button("> REBOOT_SYSTEM", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==========================
# 4. KPI HUD (Head-Up Display)
# ==========================
growth_df = returns.get("growth_curve")
cagr = returns.get("CAGR")
current_val = growth_df["Total_Value"].iloc[-1] if growth_df is not None else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Equity_Total", f"${current_val:,.0f}", delta="LIVE")
m2.metric("CAGR_Alpha", "N/A" if cagr is None else f"{cagr*100:.2f}%")
m3.metric("Positions", len(allocations.get("stock_allocation", [])))
m4.metric("Volatility", "LOW", delta="-1.2%", delta_color="inverse")

st.markdown("---")

# ==========================
# 5. MAIN INTERFACE
# ==========================
t1, t2, t3 = st.tabs(["01_PERFORMANCE", "02_ALLOCATION", "03_RAW_LOGS"])

# --- GROWTH ---
with t1:
    growth = returns.get("growth_curve")
    if growth is not None:
        # Neon Green Area Chart
        chart = alt.Chart(growth).mark_area(
            line={'color':'#10B981', 'strokeWidth': 2},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='#10B981', offset=0),
                       alt.GradientStop(color='rgba(16, 185, 129, 0)', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            x=alt.X("Date:T", axis=alt.Axis(gridColor='#1E293B', title=None)),
            y=alt.Y("Total_Value:Q", scale=alt.Scale(zero=False), axis=alt.Axis(gridColor='#1E293B', title=None)),
            tooltip=["Date:T", "Total_Value:Q"]
        ).properties(height=450).configure_view(strokeOpacity=0)
        
        st.altair_chart(chart, use_container_width=True)

# --- ALLOCATIONS ---
with t2:
    seg, stock = allocations.get("segment_allocation"), allocations.get("stock_allocation")
    c1, c2 = st.columns(2)

    with c1:
        if seg is not None:
            st.markdown("#### Sector_Distribution")
            pie = alt.Chart(seg).mark_arc(innerRadius=70, stroke="#0E1117").encode(
                theta="Segment_%:Q",
                color=alt.Color("Segment:N", scale=alt.Scale(scheme='darkmulti')),
                tooltip=["Segment", "Segment_%"]
            ).properties(height=350)
            st.altair_chart(pie, use_container_width=True)

    with c2:
        if stock is not None:
            st.markdown("#### Top_Holdings_Weight")
            bar = alt.Chart(stock.head(10)).mark_bar(color='#10B981', opacity=0.8).encode(
                x=alt.X("Stock_%:Q", axis=alt.Axis(grid=False)),
                y=alt.Y("Company_Name:N", sort="-x", axis=alt.Axis(grid=False)),
            ).properties(height=350)
            st.altair_chart(bar, use_container_width=True)

# --- RAW TABLES ---
with t3:
    for key, df in portfolio.items():
        if df is not None and not isinstance(df, dict) and not df.empty:
            st.markdown(f"**LOG_ENTRY: {key.upper()}**")
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "Stock_%": st.column_config.ProgressColumn(min_value=0, max_value=100, format="%.1f%%", color="#10B981"),
                    "Total_Value": st.column_config.NumberColumn(format="$%0.2f")
                }
            )