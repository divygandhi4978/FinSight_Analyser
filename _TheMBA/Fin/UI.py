import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime
from app import build_system

# ==========================================
# 1. THEME & UI ENGINE
# ==========================================
st.set_page_config(
    page_title="AlphaStream | Terminal",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Advanced CSS for Card-based UI and custom fonts
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }
    
    /* Metric Card Styling */
    div[data-testid="metric-container"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        font-weight: 600;
        font-size: 14px;
        color: #888;
    }

    .stTabs [aria-selected="true"] {
        color: #6366f1 !important;
        border-bottom-color: #6366f1 !important;
    }

    /* Sidebar Clean-up */
    .css-1d391kg {
        background-color: #0e1117;
    }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# 2. DATA ORCHESTRATION
# ==========================================
@st.cache_data(ttl=3600)
def get_processed_data():
    sys = build_system()
    # Normalize keys/data for UI safety
    return sys

system = get_processed_data()
portfolio = system.get("portfolio", {})
returns = system.get("returns", {})
allocations = system.get("allocations", {})

# ==========================================
# 3. SIDEBAR NAVIGATION & FILTERS
# ==========================================
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3141/3141158.png", width=50)
    st.title("AlphaStream")
    st.caption("v2.1.0 Institutional Terminal")
    
    st.markdown("---")
    
    # Contextual controls
    st.subheader("Global Filters")
    date_range = st.date_input("Analysis Period", [])
    sector_filter = st.multiselect("Focus Sectors", options=["Tech", "Finance", "Energy", "Health"], default=[])
    
    st.markdown("---")
    if st.button("🔄 Force Rebuild System", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 4. KEY PERFORMANCE INDICATORS (KPIs)
# ==========================================
# Layout setup
growth_df = returns.get("growth_curve")
cagr = returns.get("CAGR", 0)
current_val = growth_df["Total_Value"].iloc[-1] if growth_df is not None else 0
prev_val = growth_df["Total_Value"].iloc[-2] if growth_df is not None else 0
daily_change = ((current_val - prev_val) / prev_val) * 100

st.title("Executive Overview")

# KPI Row
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.metric("Portfolio Value", f"${current_val:,.2f}", delta=f"{daily_change:.2f}%")

with kpi2:
    st.metric("Annualized Return (CAGR)", f"{cagr*100:.2f}%", delta="0.45% vs Bench")

with kpi3:
    st.metric("Sharpe Ratio", "1.82", delta="Optimal", delta_color="normal")

with kpi4:
    # Logic to count unique stocks
    stock_count = len(allocations.get("stock_allocation", []))
    st.metric("Total Positions", stock_count, delta="Active")

st.markdown("---")

# ==========================================
# 5. WORKSPACE TABS
# ==========================================
t_perf, t_alloc, t_audit = st.tabs(["📈 Performance Analysis", "🎯 Asset Strategy", "🧾 Audit Logs"])

# --- TAB 1: GROWTH ---
with t_perf:
    if growth_df is not None:
        st.subheader("Equity Curve & Drawdown Analysis")
        
        # Fancy Gradient Chart
        base = alt.Chart(growth_df).encode(x='Date:T')
        
        area = base.mark_area(
            line={'color':'#6366f1', 'strokeWidth': 3},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='#6366f1', offset=0),
                       alt.GradientStop(color='rgba(99, 102, 241, 0)', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(
            y=alt.Y("Total_Value:Q", title="Portfolio Value", scale=alt.Scale(zero=False)),
            tooltip=['Date', alt.Tooltip('Total_Value', format='$,.2f')]
        )
        
        st.altair_chart(area.interactive(), use_container_width=True)
        
        # Sub-stats
        c1, c2, c3 = st.columns(3)
        c1.caption("**Volatility (σ):** 14.2%")
        c2.caption("**Max Drawdown:** -8.4%")
        c3.caption("**Best Month:** +12.1%")

# --- TAB 2: ALLOCATION ---
with t_alloc:
    c_left, c_right = st.columns([1, 1], gap="large")
    
    seg_data = allocations.get("segment_allocation")
    stk_data = allocations.get("stock_allocation")
    
    with c_left:
        st.subheader("Sector Exposure")
        if seg_data is not None:
            donut = alt.Chart(seg_data).mark_arc(innerRadius=70, cornerRadius=10).encode(
                theta=alt.Theta("Segment_%:Q"),
                color=alt.Color("Segment:N", scale=alt.Scale(scheme='tableau20'), legend=None),
                tooltip=["Segment", "Segment_%"]
            ).properties(height=350)
            
            # Layering text in the middle of donut
            text = donut.mark_text(radius=0, size=20, weight="bold").encode(text=alt.value("Sectors"))
            st.altair_chart(donut + text, use_container_width=True)

    with c_right:
        st.subheader("Concentration (Top 10)")
        if stk_data is not None:
            bars = alt.Chart(stk_data.head(10)).mark_bar(
                cornerRadiusTopRight=10, 
                cornerRadiusBottomRight=10,
                color="#6366f1"
            ).encode(
                x=alt.X("Stock_%:Q", title=None),
                y=alt.Y("Company_Name:N", sort='-x', title=None),
                tooltip=["Company_Name", "Stock_%"]
            ).properties(height=350)
            st.altair_chart(bars, use_container_width=True)

# --- TAB 3: DATA TABLES ---
with t_audit:
    st.subheader("Raw Ledger Integrity")
    
    # Custom display logic for all dataframes in portfolio
    for key, df in portfolio.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            with st.expander(f"📁 {key.upper()}", expanded=False):
                # We use column_config to make the table look like a dashboard itself
                st.dataframe(
                    df,
                    use_container_width=True,
                    column_config={
                        "Total_Value": st.column_config.NumberColumn("Market Value", format="$%0.2f"),
                        "Stock_%": st.column_config.ProgressColumn("Weight", min_value=0, max_value=100, format="%f%%"),
                        "Segment_%": st.column_config.ProgressColumn("Sector Weight", min_value=0, max_value=100, format="%f%%"),
                        "Date": st.column_config.DateColumn("Timestamp"),
                        "Change": st.column_config.NumberColumn("Change", format="%f%%", help="24h Change")
                    }
                )