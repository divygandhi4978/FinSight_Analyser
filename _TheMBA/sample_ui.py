import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# =========================================================
# PAGE CONFIG
# =========================================================
st.set_page_config(
    page_title="Healthcare Sector Intelligence 360",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =========================================================
# STYLE
# =========================================================
st.markdown(
    """
    <style>
        .block-container { padding-top: 1.1rem; padding-bottom: 2rem; }
        .section-title { font-size: 1.35rem; font-weight: 700; margin-top: 0.2rem; }
        .section-sub { color: #6b7280; margin-top: -0.2rem; margin-bottom: 0.8rem; }
        .card {
            background: linear-gradient(180deg, rgba(17,24,39,0.96), rgba(17,24,39,0.88));
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 18px;
            padding: 16px 18px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        }
        .kpi-label { color: #94a3b8; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.04em; }
        .kpi-value { font-size: 1.7rem; font-weight: 800; margin-top: 0.1rem; }
        .kpi-delta { font-size: 0.9rem; margin-top: 0.1rem; }
        .signal-buy { color: #10b981; font-weight: 700; }
        .signal-hold { color: #f59e0b; font-weight: 700; }
        .signal-sell { color: #ef4444; font-weight: 700; }
        .small-note { color: #64748b; font-size: 0.84rem; }
        .report-box {
            background: rgba(15,23,42,0.05);
            border: 1px solid rgba(148,163,184,0.25);
            border-radius: 16px;
            padding: 14px 16px;
        }
        .metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
        @media (max-width: 1100px) {
            .metric-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# CONSTANTS
# =========================================================
COMPANIES = ["Apollo Hospitals", "Fortis Healthcare", "Max Healthcare", "Narayana Health", "Rainbow Children's Medicare"]
TICKERS = {
    "Apollo Hospitals": "APOLLOHOSP",
    "Fortis Healthcare": "FORTIS",
    "Max Healthcare": "MAXHEALTH",
    "Narayana Health": "NH",
    "Rainbow Children's Medicare": "RAINBOW",
}

QUARTERS = [
    "Q1FY23", "Q2FY23", "Q3FY23", "Q4FY23",
    "Q1FY24", "Q2FY24", "Q3FY24", "Q4FY24",
    "Q1FY25", "Q2FY25", "Q3FY25", "Q4FY25",
]

THEME_ORDER = ["Growth", "Profitability", "Balance Sheet", "Cash Flow", "Valuation", "Healthcare Ops", "Risk"]

# =========================================================
# HELPERS
# =========================================================
def qoq(curr, prev):
    if prev == 0 or pd.isna(prev):
        return np.nan
    return (curr - prev) / abs(prev) * 100


def yoy(curr, prev4):
    if prev4 == 0 or pd.isna(prev4):
        return np.nan
    return (curr - prev4) / abs(prev4) * 100


def fmt(x, decimals=1, suffix=""):
    if pd.isna(x):
        return "—"
    if isinstance(x, (int, np.integer)):
        return f"{x:,}{suffix}"
    return f"{x:,.{decimals}f}{suffix}"


def trend_arrow(v):
    if pd.isna(v):
        return "→"
    return "↑" if v >= 0 else "↓"


def signal_class(label):
    label = label.upper()
    if label == "BUY":
        return "signal-buy"
    if label == "SELL":
        return "signal-sell"
    return "signal-hold"


def make_company_profile():
    profiles = pd.DataFrame([
        ["Apollo Hospitals", 2250, 680, 21.8, 16.4, 2.9, 28.5, 18.2, 6.8, 51000, 4300, 72, 2.4],
        ["Fortis Healthcare", 670, 360, 16.9, 13.2, 2.1, 24.8, 16.9, 6.0, 21500, 1800, 64, 2.1],
        ["Max Healthcare", 980, 540, 25.7, 18.8, 4.0, 30.2, 19.5, 7.5, 27800, 2400, 69, 2.7],
        ["Narayana Health", 740, 460, 18.8, 14.5, 2.7, 26.1, 17.0, 5.9, 19800, 1700, 78, 1.9],
        ["Rainbow Children's Medicare", 420, 240, 23.4, 17.1, 3.5, 31.0, 18.4, 7.2, 12200, 1100, 74, 2.5],
    ], columns=[
        "Company", "Market Cap", "Enterprise Value", "Current PE", "EV/EBITDA", "Price/Book",
        "ROCE", "ROE", "Debt/Equity", "Beds", "Patients/Quarter", "Occupancy", "ARPOB"
    ])
    profiles["Ticker"] = profiles["Company"].map(TICKERS)
    profiles["Sector"] = "Hospitals"
    return profiles


def make_quarterly_data():
    rng = np.random.default_rng(42)
    rows = []

    base = {
        "Apollo Hospitals": {"rev": 6100, "ebitda": 980, "pat": 520, "debt": 4300, "equity": 14800, "ocf": 860, "capex": 540, "beds": 7400, "occ": 71.5, "arpob": 6.6, "alos": 3.3, "doctor_cost": 22.0, "insurance_mix": 62, "digital": 68},
        "Fortis Healthcare": {"rev": 3200, "ebitda": 430, "pat": 225, "debt": 1950, "equity": 6400, "ocf": 330, "capex": 160, "beds": 4200, "occ": 63.5, "arpob": 5.7, "alos": 3.5, "doctor_cost": 24.5, "insurance_mix": 58, "digital": 61},
        "Max Healthcare": {"rev": 4050, "ebitda": 760, "pat": 345, "debt": 1700, "equity": 7200, "ocf": 540, "capex": 280, "beds": 5400, "occ": 68.3, "arpob": 7.2, "alos": 3.1, "doctor_cost": 21.4, "insurance_mix": 64, "digital": 70},
        "Narayana Health": {"rev": 2920, "ebitda": 510, "pat": 210, "debt": 1350, "equity": 6900, "ocf": 410, "capex": 190, "beds": 5800, "occ": 77.2, "arpob": 5.1, "alos": 4.0, "doctor_cost": 23.0, "insurance_mix": 55, "digital": 65},
        "Rainbow Children's Medicare": {"rev": 1180, "ebitda": 270, "pat": 120, "debt": 720, "equity": 2600, "ocf": 145, "capex": 80, "beds": 1600, "occ": 73.1, "arpob": 7.0, "alos": 2.8, "doctor_cost": 20.6, "insurance_mix": 59, "digital": 63},
    }

    for comp in COMPANIES:
        state = base[comp].copy()
        for i, q in enumerate(QUARTERS):
            season = np.sin(i / 3.2) * 0.03
            growth = 0.02 + season + rng.normal(0, 0.012)
            margin_move = rng.normal(0, 0.45)
            occ_move = rng.normal(0, 0.7)
            arpob_move = rng.normal(0, 0.08)
            alos_move = rng.normal(0, 0.05)
            debt_move = rng.normal(0, 0.04)

            if comp == "Narayana Health":
                growth += 0.005
                state["occ"] += 0.15
            if comp == "Max Healthcare":
                growth += 0.012
                margin_move += 0.1
            if comp == "Apollo Hospitals":
                growth += 0.01
            if comp == "Rainbow Children's Medicare":
                growth += 0.015
                margin_move += 0.15

            revenue = state["rev"] * (1 + growth)
            ebitda_margin = np.clip((state["ebitda"] / state["rev"]) * 100 + margin_move + np.random.uniform(-0.3, 0.3), 10, 35)
            ebitda = revenue * ebitda_margin / 100
            pat_margin = np.clip(ebitda_margin - np.random.uniform(4.5, 7.5), 2.0, 20.0)
            pat = revenue * pat_margin / 100
            debt = max(state["debt"] * (1 + debt_move), 0)
            equity = state["equity"] * (1 + np.random.uniform(0.008, 0.02))
            ocf = ebitda * np.random.uniform(0.7, 0.9)
            capex = max(state["capex"] * (1 + np.random.uniform(-0.06, 0.12)), 0)
            fcf = ocf - capex
            beds = int(state["beds"] * (1 + np.random.uniform(0.001, 0.01)))
            occ = np.clip(state["occ"] + occ_move + (i * 0.08), 55, 85)
            arpob = max(state["arpob"] + arpob_move + (growth * 8), 3.5)
            alos = np.clip(state["alos"] + alos_move + np.random.uniform(-0.03, 0.03), 2.3, 4.7)
            doctor_cost = np.clip(state["doctor_cost"] + np.random.uniform(-0.2, 0.4), 18, 30)
            insurance_mix = np.clip(state["insurance_mix"] + np.random.uniform(-1.0, 1.3), 45, 75)
            digital = np.clip(state["digital"] + np.random.uniform(0.4, 1.8), 55, 90)

            rows.append({
                "Company": comp,
                "Ticker": TICKERS[comp],
                "Quarter": q,
                "Revenue": revenue,
                "EBITDA": ebitda,
                "EBITDA Margin": ebitda_margin,
                "PAT": pat,
                "PAT Margin": pat_margin,
                "Debt": debt,
                "Equity": equity,
                "OCF": ocf,
                "Capex": capex,
                "FCF": fcf,
                "Beds": beds,
                "Occupancy": occ,
                "ARPOB": arpob,
                "ALOS": alos,
                "Doctor Cost Index": doctor_cost,
                "Insurance Mix": insurance_mix,
                "Digital Adoption": digital,
                "Revenue Growth QoQ": np.nan,
                "Revenue Growth YoY": np.nan,
                "EBITDA Growth QoQ": np.nan,
                "PAT Growth QoQ": np.nan,
            })

            state.update({"rev": revenue, "ebitda": ebitda, "pat": pat, "debt": debt, "equity": equity,
                          "ocf": ocf, "capex": capex, "beds": beds, "occ": occ, "arpob": arpob, "alos": alos,
                          "doctor_cost": doctor_cost, "insurance_mix": insurance_mix, "digital": digital})

    df = pd.DataFrame(rows)
    df.sort_values(["Company", "Quarter"], inplace=True)
    df.reset_index(drop=True, inplace=True)

    for comp in COMPANIES:
        idx = df["Company"] == comp
        sub = df.loc[idx].copy().reset_index()
        sub["Revenue Growth QoQ"] = sub["Revenue"].pct_change() * 100
        sub["Revenue Growth YoY"] = sub["Revenue"].pct_change(4) * 100
        sub["EBITDA Growth QoQ"] = sub["EBITDA"].pct_change() * 100
        sub["PAT Growth QoQ"] = sub["PAT"].pct_change() * 100
        df.loc[idx, ["Revenue Growth QoQ", "Revenue Growth YoY", "EBITDA Growth QoQ", "PAT Growth QoQ"]] = sub[["Revenue Growth QoQ", "Revenue Growth YoY", "EBITDA Growth QoQ", "PAT Growth QoQ"]].values
    return df


def make_comps(qdf):
    latest_q = qdf["Quarter"].unique()[-1]
    prev_q = qdf["Quarter"].unique()[-2]
    latest = qdf[qdf["Quarter"] == latest_q].copy()
    prev = qdf[qdf["Quarter"] == prev_q].copy()

    out = latest[["Company", "Ticker", "Revenue", "EBITDA", "EBITDA Margin", "PAT", "Debt", "Equity", "OCF", "Capex", "FCF", "Beds", "Occupancy", "ARPOB", "ALOS", "Doctor Cost Index", "Insurance Mix", "Digital Adoption"]].copy()
    out = out.merge(prev[["Company", "Revenue", "EBITDA", "PAT", "Occupancy", "ARPOB"]], on="Company", suffixes=("", " Prev"))
    out["Revenue QoQ %"] = (out["Revenue"] / out["Revenue Prev"] - 1) * 100
    out["EBITDA QoQ %"] = (out["EBITDA"] / out["EBITDA Prev"] - 1) * 100
    out["PAT QoQ %"] = (out["PAT"] / out["PAT Prev"] - 1) * 100
    out["Debt/Equity"] = out["Debt"] / out["Equity"]
    out["ROCE"] = (out["EBITDA"] * 0.72) / (out["Debt"] + out["Equity"]) * 100
    out["ROE"] = out["PAT"] / out["Equity"] * 100
    out["EV/EBITDA"] = np.where(out["EBITDA"] > 0, (out["Debt"] + out["Equity"]) / out["EBITDA"], np.nan)
    out["PE"] = np.where(out["PAT"] > 0, (out["Debt"] + out["Equity"]) / out["PAT"], np.nan)
    out["Market Cap"] = out["Equity"] * np.random.uniform(1.45, 2.05, len(out))
    out["Risk Score"] = np.clip((out["Debt/Equity"] * 15) + (75 - out["Occupancy"]) * 0.8 + (25 - out["EBITDA Margin"]) * 1.2, 10, 90)
    out["Moat Score"] = np.clip((out["Digital Adoption"] * 0.4) + (out["Occupancy"] * 0.35) + (out["ROCE"] * 0.5), 20, 95)
    return out.sort_values("Moat Score", ascending=False).reset_index(drop=True), latest_q, prev_q


def make_peers_table(comp_df):
    cols = [
        "Company", "Revenue QoQ %", "EBITDA QoQ %", "PAT QoQ %", "EBITDA Margin", "ROCE", "ROE",
        "Debt/Equity", "Occupancy", "ARPOB", "ALOS", "Digital Adoption", "Risk Score", "Moat Score"
    ]
    peer = comp_df[cols].copy()
    peer["Growth Rank"] = peer["Revenue QoQ %"].rank(ascending=False, method="min")
    peer["Profitability Rank"] = peer["EBITDA Margin"].rank(ascending=False, method="min")
    peer["Risk Rank"] = peer["Risk Score"].rank(ascending=True, method="min")
    peer["Overall Rank"] = (peer["Growth Rank"] + peer["Profitability Rank"] + peer["Risk Rank"]) / 3
    return peer.sort_values("Overall Rank").reset_index(drop=True)


def make_sector_aggregates(qdf):
    agg = qdf.groupby("Quarter").agg({
        "Revenue": "sum",
        "EBITDA": "sum",
        "PAT": "sum",
        "Debt": "sum",
        "Equity": "sum",
        "OCF": "sum",
        "Capex": "sum",
        "Beds": "sum",
        "Occupancy": "mean",
        "ARPOB": "mean",
        "ALOS": "mean",
        "Doctor Cost Index": "mean",
        "Insurance Mix": "mean",
        "Digital Adoption": "mean",
    }).reset_index()
    agg["EBITDA Margin"] = agg["EBITDA"] / agg["Revenue"] * 100
    agg["PAT Margin"] = agg["PAT"] / agg["Revenue"] * 100
    agg["Debt/Equity"] = agg["Debt"] / agg["Equity"]
    agg["FCF"] = agg["OCF"] - agg["Capex"]
    agg["ROCE"] = (agg["EBITDA"] * 0.72) / (agg["Debt"] + agg["Equity"]) * 100
    agg["Revenue QoQ"] = agg["Revenue"].pct_change() * 100
    agg["EBITDA QoQ"] = agg["EBITDA"].pct_change() * 100
    agg["PAT QoQ"] = agg["PAT"].pct_change() * 100
    return agg


def dcf_model(base_rev, base_ebitda_margin, years=5):
    # Static illustrative model only.
    rev_growth = [0.13, 0.11, 0.10, 0.08, 0.07]
    margin_expansion = [0.2, 0.3, 0.3, 0.2, 0.1]
    tax = 0.25
    wc_ratio = 0.03
    capex_ratio = 0.06
    dep_ratio = 0.03
    wacc = 0.11
    tg = 0.05

    rows = []
    rev = base_rev
    margin = base_ebitda_margin
    for i in range(years):
        rev *= (1 + rev_growth[i])
        margin = min(margin + margin_expansion[i], 30)
        ebitda = rev * margin / 100
        ebit = ebitda - rev * dep_ratio
        nopat = ebit * (1 - tax)
        reinvestment = rev * (capex_ratio + wc_ratio)
        fcff = nopat + rev * dep_ratio - reinvestment
        discount = 1 / ((1 + wacc) ** (i + 1))
        pv = fcff * discount
        rows.append([f"FY{i+1}", rev, margin, ebitda, fcff, discount, pv])

    terminal_fcff = rows[-1][4] * (1 + tg)
    terminal_value = terminal_fcff / (wacc - tg)
    pv_terminal = terminal_value / ((1 + wacc) ** years)
    equity_value = sum(r[-1] for r in rows) + pv_terminal
    return pd.DataFrame(rows, columns=["Year", "Revenue", "EBITDA Margin", "EBITDA", "FCFF", "Discount Factor", "PV of FCFF"]), equity_value, wacc, tg, pv_terminal


def risk_register(company):
    risks = {
        "Apollo Hospitals": [
            ["Doctor cost inflation", "Medium", "Stable", "Compensation pressure in metro hospitals."],
            ["Capital intensity", "Medium", "Rising", "Expansion requires sustained capex discipline."],
            ["Insurance mix dependency", "Low", "Stable", "Pricing resilience remains manageable."],
            ["Regulatory pricing pressure", "Medium", "Stable", "Policy changes may affect discretionary procedure mix."],
        ],
        "Fortis Healthcare": [
            ["Competitive occupancy pressure", "Medium", "Improving", "Utilization still below premium peers."],
            ["Margin normalization", "High", "Rising", "Margins remain sensitive to fixed-cost absorption."],
            ["Debt sensitivity", "Medium", "Stable", "Balance sheet still needs discipline."],
            ["Doctor retention", "Medium", "Stable", "Specialist retention affects premium case mix."],
        ],
        "Max Healthcare": [
            ["High valuation base", "High", "Stable", "Premium multiple leaves less room for execution error."],
            ["Metro concentration", "Medium", "Stable", "Demand concentration in top cities can amplify cyclicality."],
            ["Capex execution", "Medium", "Improving", "New bed additions must convert into occupancy."],
            ["Cost inflation", "Medium", "Rising", "Salaries and consumables remain watch items."],
        ],
        "Narayana Health": [
            ["Lower ARPOB", "Medium", "Stable", "High-volume model pressures pricing power."],
            ["Case mix volatility", "Medium", "Stable", "Mix shift impacts profitability."],
            ["Expansion execution", "Medium", "Rising", "New capacity must be absorbed efficiently."],
            ["Regional dependence", "Low", "Stable", "Performance linked to select markets."],
        ],
        "Rainbow Children's Medicare": [
            ["Specialty concentration", "Medium", "Stable", "Pediatric focus is strong but narrower."],
            ["Capacity ramp-up", "Medium", "Improving", "New beds need utilization catch-up."],
            ["High growth expectations", "High", "Rising", "Market pricing already embeds strong execution."],
            ["Doctor franchise dependency", "Medium", "Stable", "Specialist-led model must retain talent."],
        ],
    }
    return pd.DataFrame(risks[company], columns=["Risk", "Severity", "Trend", "Evidence"])


# =========================================================
# DATA BUILD
# =========================================================
company_profile = make_company_profile()
quarterly = make_quarterly_data()
company_cards, latest_q, prev_q = make_comps(quarterly)
peer_table = make_peers_table(company_cards)
sector = make_sector_aggregates(quarterly)
latest = quarterly[quarterly["Quarter"] == latest_q].copy()
prev = quarterly[quarterly["Quarter"] == prev_q].copy()

# Use the strongest company as default deep-dive anchor unless user changes it.
default_company = company_cards.sort_values("Moat Score", ascending=False).iloc[0]["Company"]

# =========================================================
# SIDEBAR CONTROL TOWER
# =========================================================
st.sidebar.title("Control Tower")
st.sidebar.caption("Static analyst terminal — quarter-ready and structure-first")

company_pick = st.sidebar.selectbox("Company", COMPANIES, index=COMPANIES.index(default_company))
quarter_pick = st.sidebar.selectbox("Quarter", QUARTERS, index=len(QUARTERS) - 1)
peer_focus = st.sidebar.multiselect("Peer Set", COMPANIES, default=COMPANIES)
metric_focus = st.sidebar.multiselect(
    "Metric Lens",
    ["Financials", "Operations", "Balance Sheet", "Cash Flow", "Valuation", "Risk"],
    default=["Financials", "Operations", "Balance Sheet", "Cash Flow", "Valuation", "Risk"],
)
show_raw = st.sidebar.toggle("Show raw tables", False)

# =========================================================
# HEADER
# =========================================================
st.title("🏥 Healthcare Sector Intelligence 360")
st.caption("Institutional-style sector comparison platform for Indian hospital chains")
st.markdown(
    f"""
    <div class='report-box'>
        <b>Coverage:</b> Indian hospital chains &nbsp;|&nbsp;
        <b>Universe:</b> {len(COMPANIES)} companies &nbsp;|&nbsp;
        <b>Latest quarter:</b> {latest_q} &nbsp;|&nbsp;
        <b>Update mode:</b> Static prototype with dummy data
    </div>
    """,
    unsafe_allow_html=True,
)

# =========================================================
# TOP KPIs
# =========================================================
sel_latest = quarterly[(quarterly["Company"] == company_pick) & (quarterly["Quarter"] == quarter_pick)].iloc[0]
sel_prev = quarterly[(quarterly["Company"] == company_pick)].sort_values("Quarter")
current_idx = sel_prev.index[sel_prev["Quarter"] == quarter_pick][0]
prev_row = sel_prev.loc[current_idx - 1] if current_idx > sel_prev.index.min() else None
prev4_row = sel_prev.loc[current_idx - 4] if current_idx - 4 in sel_prev.index else None

rev_qoq = qoq(sel_latest["Revenue"], prev_row["Revenue"] if prev_row is not None else np.nan)
ebitda_qoq = qoq(sel_latest["EBITDA"], prev_row["EBITDA"] if prev_row is not None else np.nan)
pat_qoq = qoq(sel_latest["PAT"], prev_row["PAT"] if prev_row is not None else np.nan)
rev_yoy = yoy(sel_latest["Revenue"], prev4_row["Revenue"] if prev4_row is not None else np.nan)
occ_qoq = qoq(sel_latest["Occupancy"], prev_row["Occupancy"] if prev_row is not None else np.nan)

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Revenue", fmt(sel_latest["Revenue"], 0), f"{trend_arrow(rev_qoq)} {fmt(rev_qoq, 1)}% QoQ")
k2.metric("EBITDA Margin", f"{sel_latest['EBITDA Margin']:.1f}%", f"{trend_arrow(ebitda_qoq)} {fmt(ebitda_qoq, 1)}% QoQ")
k3.metric("PAT", fmt(sel_latest["PAT"], 0), f"{trend_arrow(pat_qoq)} {fmt(pat_qoq, 1)}% QoQ")
k4.metric("Occupancy", f"{sel_latest['Occupancy']:.1f}%", f"{trend_arrow(occ_qoq)} {fmt(occ_qoq, 1)}% QoQ")
k5.metric("ROCE", f"{company_cards.loc[company_cards['Company']==company_pick, 'ROCE'].iloc[0]:.1f}%", "vs peers")
k6.metric("Risk Score", f"{company_cards.loc[company_cards['Company']==company_pick, 'Risk Score'].iloc[0]:.0f}", "higher = worse")

st.markdown("---")

# =========================================================
# TABS
# =========================================================
tabs = st.tabs([
    "Sector Command Center",
    "Peer Comparison",
    "Company Deep Dive",
    "Valuation & DCF",
    "Risk Intelligence",
    "Geo Footprint",
    "Data Room",
])

# =========================================================
# TAB 1 — SECTOR COMMAND CENTER
# =========================================================
with tabs[0]:
    st.markdown("<div class='section-title'>Sector Command Center</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>What a serious investor sees first: momentum, margins, leverage, capacity, and valuation regime.</div>", unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Sector Revenue", fmt(sector.iloc[-1]['Revenue'], 0), f"QoQ {fmt(sector.iloc[-1]['Revenue QoQ'], 1)}%")
    s2.metric("Sector EBITDA Margin", f"{sector.iloc[-1]['EBITDA Margin']:.1f}%", f"QoQ {fmt(sector.iloc[-1]['EBITDA QoQ'], 1)}%")
    s3.metric("Sector Occupancy", f"{sector.iloc[-1]['Occupancy']:.1f}%", f"QoQ {fmt(sector.iloc[-1]['Occupancy'] - sector.iloc[-2]['Occupancy'], 1)} pts")
    s4.metric("Sector Debt/Equity", f"{sector.iloc[-1]['Debt/Equity']:.2f}x", f"QoQ {fmt(sector.iloc[-1]['Debt/Equity'] - sector.iloc[-2]['Debt/Equity'], 2)}x")

    c1, c2 = st.columns([2, 1])
    with c1:
        fig = go.Figure()
        for comp in COMPANIES:
            d = quarterly[quarterly["Company"] == comp]
            fig.add_trace(go.Scatter(x=d["Quarter"], y=d["Revenue"], mode="lines+markers", name=comp))
        fig.update_layout(title="Revenue Trend by Company", xaxis_title="Quarter", yaxis_title="Revenue", hovermode="x unified", height=420)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = go.Figure()
        for comp in COMPANIES:
            d = quarterly[quarterly["Company"] == comp]
            fig.add_trace(go.Scatter(x=d["Quarter"], y=d["EBITDA Margin"], mode="lines+markers", name=comp))
        fig.update_layout(title="EBITDA Margin Trend", xaxis_title="Quarter", yaxis_title="Margin %", hovermode="x unified", height=420)
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=sector["Quarter"], y=sector["Beds"], name="Beds"))
        fig.add_trace(go.Bar(x=sector["Quarter"], y=sector["Occupancy"], name="Occupancy %", yaxis="y2"))
        fig.update_layout(
            title="Capacity and Utilization",
            yaxis=dict(title="Beds"),
            yaxis2=dict(title="Occupancy %", overlaying="y", side="right"),
            barmode="group",
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        fig = px.box(company_cards, y="EV/EBITDA", points="all", title="Valuation Dispersion: EV/EBITDA")
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    leader = company_cards[["Company", "Revenue QoQ %", "EBITDA Margin", "ROCE", "Debt/Equity", "Risk Score", "Moat Score"]].copy()
    leader = leader.sort_values(["Moat Score", "ROCE"], ascending=False)
    st.subheader("Sector Leaderboard")
    st.dataframe(leader, use_container_width=True, hide_index=True)

    st.markdown("#### Analyst commentary")
    st.markdown(
        f"""
        <div class='report-box'>
        <b>Sector read:</b> Healthcare remains structurally supported by occupancy stability, urban demand density, and insurance penetration.
        The market still rewards operators that combine high occupancy, disciplined capex, and premium case mix.
        For this universe, margin quality and balance-sheet discipline matter more than raw revenue size.
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# TAB 2 — PEER COMPARISON
# =========================================================
with tabs[1]:
    st.markdown("<div class='section-title'>Peer Comparison</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Side-by-side relative positioning — the core of institutional screening.</div>", unsafe_allow_html=True)

    comp = company_cards[company_cards["Company"].isin(peer_focus)].copy()

    a, b = st.columns([1.6, 1])
    with a:
        fig = px.scatter(
            comp,
            x="Revenue QoQ %",
            y="ROCE",
            size="Market Cap",
            color="EBITDA Margin",
            hover_name="Company",
            text="Ticker",
            title="Growth vs Capital Efficiency",
            size_max=45,
        )
        fig.update_traces(textposition="top center")
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

    with b:
        radar_cols = ["EBITDA Margin", "ROCE", "ROE", "Occupancy", "Digital Adoption", "ARPOB"]
        fig = go.Figure()
        for comp_name in comp["Company"].tolist():
            row = company_cards[company_cards["Company"] == comp_name].iloc[0]
            vals = [row[c] for c in radar_cols]
            fig.add_trace(go.Scatterpolar(r=vals + [vals[0]], theta=radar_cols + [radar_cols[0]], fill="toself", name=comp_name))
        fig.update_layout(title="Operating / Quality Radar", polar=dict(radialaxis=dict(visible=True)), height=500)
        st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        order = company_cards.sort_values("EBITDA Margin", ascending=False)
        fig = px.bar(order, x="Company", y=["EBITDA Margin", "ROCE"], barmode="group", title="Margin and ROCE Comparison")
        fig.update_layout(height=430)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(
            company_cards.sort_values("Risk Score", ascending=True),
            x="Company",
            y="Risk Score",
            color="Risk Score",
            title="Risk Ranking (Lower is Better)",
        )
        fig.update_layout(height=430)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Peer Ranking Table")
    st.dataframe(peer_table, use_container_width=True, hide_index=True)

    st.markdown("#### Analyst commentary")
    st.markdown(
        """
        <div class='report-box'>
        The peer table should do more than rank companies. It should explain why a company ranks well: higher occupancy, cleaner margins, stronger ROCE, and less leverage.
        If the dashboard cannot answer that in one glance, it is not research-grade.
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# TAB 3 — COMPANY DEEP DIVE
# =========================================================
with tabs[2]:
    st.markdown("<div class='section-title'>Company Deep Dive</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>A full research note in dashboard form.</div>", unsafe_allow_html=True)

    current = quarterly[(quarterly["Company"] == company_pick) & (quarterly["Quarter"] <= quarter_pick)].copy()
    current = current.sort_values("Quarter")
    current_latest = current.iloc[-1]
    current_prev = current.iloc[-2] if len(current) > 1 else None
    current_prev4 = current.iloc[-5] if len(current) > 4 else None

    top = company_profile[company_profile["Company"] == company_pick].iloc[0]
    comp_row = company_cards[company_cards["Company"] == company_pick].iloc[0]

    x1, x2, x3, x4 = st.columns(4)
    x1.metric("Market Cap", f"₹{top['Market Cap']:,} Cr")
    x2.metric("Enterprise Value", f"₹{top['Enterprise Value']:,} Cr")
    x3.metric("Current PE", f"{top['Current PE']:.1f}x")
    x4.metric("EV/EBITDA", f"{top['EV/EBITDA']:.1f}x")

    y1, y2, y3, y4 = st.columns(4)
    y1.metric("ROCE", f"{top['ROCE']:.1f}%")
    y2.metric("ROE", f"{top['ROE']:.1f}%")
    y3.metric("Debt/Equity", f"{top['Debt/Equity']:.1f}x")
    y4.metric("Occupancy", f"{top['Occupancy']:.0f}%")

    c1, c2 = st.columns([1.2, 1])
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=current["Quarter"], y=current["Revenue"], name="Revenue", mode="lines+markers"))
        fig.add_trace(go.Scatter(x=current["Quarter"], y=current["Revenue Growth QoQ"], name="Revenue QoQ %", mode="lines+markers", yaxis="y2"))
        fig.update_layout(
            title=f"{company_pick}: Revenue and Growth Trend",
            yaxis=dict(title="Revenue"),
            yaxis2=dict(title="QoQ %", overlaying="y", side="right"),
            hovermode="x unified",
            height=430,
        )
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=current["Quarter"], y=current["EBITDA"], name="EBITDA"))
        fig.add_trace(go.Scatter(x=current["Quarter"], y=current["EBITDA Margin"], name="EBITDA Margin %", yaxis="y2", mode="lines+markers"))
        fig.update_layout(
            title="EBITDA and Margin",
            yaxis=dict(title="EBITDA"),
            yaxis2=dict(title="Margin %", overlaying="y", side="right"),
            hovermode="x unified",
            height=430,
        )
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        fig = go.Figure()
        fig.add_trace(go.Bar(x=current["Quarter"], y=current["OCF"], name="OCF"))
        fig.add_trace(go.Bar(x=current["Quarter"], y=current["Capex"], name="Capex"))
        fig.add_trace(go.Bar(x=current["Quarter"], y=current["FCF"], name="FCF"))
        fig.update_layout(title="Cash Flow Bridge (Quarterly)", barmode="group", height=430)
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=current["Quarter"], y=current["Occupancy"], name="Occupancy", mode="lines+markers"))
        fig.add_trace(go.Scatter(x=current["Quarter"], y=current["ARPOB"], name="ARPOB", mode="lines+markers", yaxis="y2"))
        fig.update_layout(
            title="Healthcare Operating Metrics",
            yaxis=dict(title="Occupancy %"),
            yaxis2=dict(title="ARPOB", overlaying="y", side="right"),
            hovermode="x unified",
            height=430,
        )
        st.plotly_chart(fig, use_container_width=True)

    c5, c6 = st.columns(2)
    with c5:
        fig = px.line(current, x="Quarter", y=["Debt", "Equity"], markers=True, title="Balance Sheet Evolution")
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)
    with c6:
        fig = px.line(current, x="Quarter", y=["Doctor Cost Index", "Digital Adoption", "Insurance Mix"], markers=True, title="Operating Quality Markers")
        fig.update_layout(height=420)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Company Snapshot Table")
    snapshot = current[["Quarter", "Revenue", "Revenue Growth QoQ", "EBITDA", "EBITDA Margin", "PAT", "PAT Margin", "Debt", "OCF", "Capex", "FCF", "Occupancy", "ARPOB", "ALOS"]].copy()
    st.dataframe(snapshot, use_container_width=True, hide_index=True)

    st.markdown("#### Analyst commentary")
    st.markdown(
        f"""
        <div class='report-box'>
        <b>{company_pick}</b> should be read as a quality-growth business, not just a hospital operator.
        The key question is whether revenue growth is converting into durable margin expansion and better cash conversion.
        If occupancy rises while ARPOB stays strong and leverage remains controlled, the equity story is intact.
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# TAB 4 — VALUATION & DCF
# =========================================================
with tabs[3]:
    st.markdown("<div class='section-title'>Valuation & DCF</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>Static illustrative intrinsic value framework with sensitivity logic.</div>", unsafe_allow_html=True)

    base_rev = float(current_latest["Revenue"])
    base_margin = float(current_latest["EBITDA Margin"])
    proj, equity_value, wacc, tg, pv_terminal = dcf_model(base_rev, base_margin, years=5)

    # Convert to per-share style output via a simple static divisor.
    shares = {
        "Apollo Hospitals": 140,
        "Fortis Healthcare": 74,
        "Max Healthcare": 98,
        "Narayana Health": 76,
        "Rainbow Children's Medicare": 34,
    }[company_pick]
    intrinsic_price = equity_value / shares
    current_price = intrinsic_price * np.random.uniform(0.84, 1.12)
    upside = (intrinsic_price / current_price - 1) * 100
    mos = upside - 15

    v1, v2, v3, v4 = st.columns(4)
    v1.metric("Intrinsic Value / Share", f"₹{intrinsic_price:,.0f}")
    v2.metric("Current Reference Price", f"₹{current_price:,.0f}")
    v3.metric("Upside / Downside", f"{upside:+.1f}%")
    v4.metric("Margin of Safety", f"{mos:+.1f}%")

    p1, p2 = st.columns([1.2, 1])
    with p1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=proj["Year"], y=proj["Revenue"], mode="lines+markers", name="Revenue"))
        fig.add_trace(go.Scatter(x=proj["Year"], y=proj["FCFF"], mode="lines+markers", name="FCFF", yaxis="y2"))
        fig.update_layout(
            title="DCF Projection Path",
            yaxis=dict(title="Revenue"),
            yaxis2=dict(title="FCFF", overlaying="y", side="right"),
            hovermode="x unified",
            height=430,
        )
        st.plotly_chart(fig, use_container_width=True)
    with p2:
        st.subheader("DCF Assumptions")
        dcf_assumptions = pd.DataFrame({
            "Parameter": ["Base revenue", "Base EBITDA margin", "WACC", "Terminal growth", "Tax rate", "Capex ratio", "WC ratio"],
            "Value": [f"₹{base_rev:,.0f} Cr", f"{base_margin:.1f}%", f"{wacc*100:.1f}%", f"{tg*100:.1f}%", "25.0%", "6.0%", "3.0%"],
        })
        st.dataframe(dcf_assumptions, use_container_width=True, hide_index=True)

    wacc_grid = np.arange(9.0, 13.1, 0.5)
    tg_grid = np.arange(3.0, 6.6, 0.5)
    heat = pd.DataFrame(index=[f"{x:.1f}%" for x in wacc_grid], columns=[f"{x:.1f}%" for x in tg_grid])
    for w in wacc_grid:
        for g in tg_grid:
            # Approximate sensitivity by adjusting base intrinsic
            adj = intrinsic_price * (1 + (5.5 - g) * 0.06) * (1 - (w - 11.0) * 0.08)
            heat.loc[f"{w:.1f}%", f"{g:.1f}%"] = round(adj, 0)

    fig = px.imshow(
        heat.astype(float),
        text_auto=True,
        aspect="auto",
        color_continuous_scale="RdYlGn",
        title="DCF Sensitivity: Intrinsic Value / Share",
    )
    fig.update_layout(height=500)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Valuation commentary")
    st.markdown(
        f"""
        <div class='report-box'>
        Base case supports an intrinsic value of <b>₹{intrinsic_price:,.0f}</b> per share for {company_pick} under the static assumptions used here.
        The model is intentionally conservative and should be treated as a framework, not a price target.
        Real market work would cross-check this against trading multiples, sector cycle, and execution quality.
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# TAB 5 — RISK INTELLIGENCE
# =========================================================
with tabs[4]:
    st.markdown("<div class='section-title'>Risk Intelligence</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>LLM-style risk register layout. Static text now, dynamic extraction later.</div>", unsafe_allow_html=True)

    risk_df = risk_register(company_pick)
    r1, r2 = st.columns([1.2, 1])
    with r1:
        st.subheader("Risk Register")
        st.dataframe(risk_df, use_container_width=True, hide_index=True)
    with r2:
        severity_counts = risk_df["Severity"].value_counts().reindex(["Low", "Medium", "High"]).fillna(0)
        fig = px.bar(x=severity_counts.index, y=severity_counts.values, title="Risk Severity Mix")
        fig.update_layout(height=340, xaxis_title="Severity", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)

    fig = px.line(current, x="Quarter", y=["Debt", "Doctor Cost Index", "Digital Adoption"], markers=True, title="Key Risk Drivers Over Time")
    fig.update_layout(height=410)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Risk note")
    st.markdown(
        """
        <div class='report-box'>
        Risk should be written like an analyst writes it: what is happening, why it matters, whether it is improving or worsening, and what data would confirm or reject the concern.
        A dashboard without an actual risk memo is decoration.
        </div>
        """,
        unsafe_allow_html=True,
    )

# =========================================================
# TAB 6 — GEO FOOTPRINT
# =========================================================
with tabs[5]:
    st.markdown("<div class='section-title'>Geographic Footprint</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>A static network map placeholder for hospital cluster economics and regional concentration.</div>", unsafe_allow_html=True)

    geo = pd.DataFrame([
        ["Apollo Hospitals", "Chennai", 13.0827, 80.2707, 680, 92],
        ["Apollo Hospitals", "Hyderabad", 17.3850, 78.4867, 510, 84],
        ["Fortis Healthcare", "Gurgaon", 28.4595, 77.0266, 1000, 76],
        ["Fortis Healthcare", "Mumbai", 19.0760, 72.8777, 450, 68],
        ["Max Healthcare", "Delhi", 28.7041, 77.1025, 550, 89],
        ["Max Healthcare", "Saket", 28.5244, 77.2066, 410, 87],
        ["Narayana Health", "Bangalore", 12.9716, 77.5946, 1400, 71],
        ["Narayana Health", "Kolkata", 22.5726, 88.3639, 900, 66],
        ["Rainbow Children's Medicare", "Hyderabad", 17.3850, 78.4867, 350, 80],
        ["Rainbow Children's Medicare", "Chennai", 13.0827, 80.2707, 220, 75],
    ], columns=["Company", "City", "lat", "lon", "Beds", "Revenue Index"])

    geo_focus = geo[geo["Company"].isin(peer_focus)]
    fig = px.scatter_mapbox(
        geo_focus,
        lat="lat",
        lon="lon",
        size="Beds",
        color="Revenue Index",
        hover_name="City",
        hover_data=["Company", "Beds", "Revenue Index"],
        zoom=4.2,
        height=620,
        mapbox_style="open-street-map",
        title="Hospital Cluster Footprint",
        color_continuous_scale="Viridis",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Regional concentration table")
    reg = geo_focus.groupby(["Company", "City"]).agg({"Beds": "sum", "Revenue Index": "mean"}).reset_index()
    st.dataframe(reg, use_container_width=True, hide_index=True)

# =========================================================
# TAB 7 — DATA ROOM
# =========================================================
with tabs[6]:
    st.markdown("<div class='section-title'>Data Room</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-sub'>This is the validation surface. Analysts need clean raw tables, not just pretty charts.</div>", unsafe_allow_html=True)

    if show_raw:
        st.subheader("Quarterly Dataset")
        st.dataframe(quarterly, use_container_width=True, hide_index=True)
        st.subheader("Company Profile Table")
        st.dataframe(company_profile, use_container_width=True, hide_index=True)
    else:
        st.info("Turn on 'Show raw tables' in the sidebar to inspect the underlying dataset.")

    st.subheader("Static master checklist for real implementation")
    checklist = pd.DataFrame([
        ["Quarterly financials", "Revenue, EBITDA, PAT, margins, OCF, Capex, FCF"],
        ["Balance sheet", "Debt, equity, cash, leverage ratios"],
        ["Operating metrics", "Beds, occupancy, ARPOB, ALOS, digital adoption"],
        ["Valuation", "PE, EV/EBITDA, DCF, sensitivity matrix"],
        ["Risk", "Severity, trend, evidence, analyst commentary"],
        ["Peer ranking", "Growth, quality, leverage, valuation, risk"],
        ["Geo footprint", "Regional concentration and capacity map"],
    ], columns=["Module", "Fields"])
    st.dataframe(checklist, use_container_width=True, hide_index=True)

# =========================================================
# FOOTER
# =========================================================
st.markdown("---")
st.markdown(
    f"""
    <div class='small-note'>
        Built as a static analyst terminal prototype. Replace dummy data with parser output quarter by quarter.
        Last rendered: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    </div>
    """,
    unsafe_allow_html=True,
)
