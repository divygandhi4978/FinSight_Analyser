import streamlit as st
import plotly.express as px
import pandas as pd



# =====================================
# SAFE FORMATTERS
# =====================================

def safe_pct(x):

    if x is None:

        return "N/A"

    if pd.isna(x):

        return "N/A"

    return f"{x:.2%}"



def safe_float(x):

    if x is None:

        return "N/A"

    if pd.isna(x):

        return "N/A"

    return f"{x:.4f}"



# =====================================
# MAIN PAGE
# =====================================

def render_research_page(system):

    st.title("Portfolio Research Dashboard")

    research = system.get("research")

    if not research:

        st.warning("Research data unavailable")

        return



    monthly = research.get("monthly")

    risk = research.get("risk")

    conc = research.get("concentration")

    drift = research.get("drift")



    if monthly is None or len(monthly) < 2:

        st.warning("Not enough history data")

        return



    # =====================================
    # KPI SECTION
    # =====================================

    st.subheader("Risk Analytics")

    c1, c2, c3 = st.columns(3)

    vol = risk.get("Volatility")
    var = risk.get("VaR_95")
    mdd = risk.get("Max_Drawdown")

    c1.metric(
        "Volatility",
        safe_pct(vol)
    )

    c2.metric(
        "VaR (95%)",
        safe_pct(var)
    )

    c3.metric(
        "Max Drawdown",
        safe_pct(mdd)
    )



    st.divider()



    # =====================================
    # PORTFOLIO VALUE
    # =====================================

    if "Date" in monthly.columns and "Total_Value" in monthly.columns:

        st.subheader("Portfolio Growth")

        fig_growth = px.line(

            monthly,

            x="Date",

            y="Total_Value",

            title="Portfolio Value Over Time"

        )

        st.plotly_chart(

            fig_growth,

            use_container_width=True

        )



    # =====================================
    # MONTHLY RETURNS
    # =====================================

    if "Monthly_Return" in monthly.columns:

        st.subheader("Monthly Returns")

        fig_returns = px.bar(

            monthly,

            x="Date",

            y="Monthly_Return",

            title="Monthly Performance"

        )

        st.plotly_chart(

            fig_returns,

            use_container_width=True

        )



    # =====================================
    # DRAWDOWN
    # =====================================

    if "Drawdown" in monthly.columns:

        st.subheader("Drawdown Curve")

        fig_dd = px.line(

            monthly,

            x="Date",

            y="Drawdown",

            title="Drawdown Behaviour"

        )

        st.plotly_chart(

            fig_dd,

            use_container_width=True

        )



    # =====================================
    # DRIFT
    # =====================================

    if drift is not None:

        if "MoM_Change" in drift.columns:

            st.subheader("Allocation Drift (MoM)")

            fig_drift = px.line(

                drift,

                x="Date",

                y="MoM_Change",

                title="Month-over-Month Drift"

            )

            st.plotly_chart(

                fig_drift,

                use_container_width=True

            )



    # =====================================
    # RETURN DISTRIBUTION
    # =====================================

    if "Monthly_Return" in monthly.columns:

        st.subheader("Return Distribution")

        fig_hist = px.histogram(

            monthly,

            x="Monthly_Return",

            nbins=min(len(monthly), 50),

            title="Return Distribution"

        )

        st.plotly_chart(

            fig_hist,

            use_container_width=True

        )



    # =====================================
    # CONCENTRATION
    # =====================================

    if conc:

        st.subheader("Concentration Risk")

        c4, c5 = st.columns(2)

        c4.metric(
            "Top 5 Weight",
            safe_pct(conc.get("Top5_Weight"))
        )

        c5.metric(
            "HHI Index",
            safe_float(conc.get("HHI"))
        )



        weights_df = conc.get("weights_df")

        if weights_df is not None:

            if "Company_Name" in weights_df.columns:

                fig_conc = px.bar(

                    weights_df.head(10),

                    x="Weight",

                    y="Company_Name",

                    orientation="h",

                    title="Top Holdings Concentration"

                )

                fig_conc.update_layout(

                    yaxis=dict(

                        autorange="reversed"

                    )

                )

                st.plotly_chart(

                    fig_conc,

                    use_container_width=True

                )