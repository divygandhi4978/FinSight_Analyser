import streamlit as st
import plotly.express as px


def render_performance(system):

    performance = system.get("performance", {})

    if not performance:

        st.error(
            "Performance data missing. "
            "Check history_daily dataset."
        )

        return


    df = performance.get("performance_df")

    metrics = performance.get("metrics")


    if df is None or df.empty:

        st.error(
            "Performance dataset empty."
        )

        return


    st.title("Performance Analytics")

    st.divider()


    # =========================
    # KPI METRICS
    # =========================

    if metrics is not None:

        cols = st.columns(len(metrics))

        for i, row in metrics.iterrows():

            val = row["Value"]

            if isinstance(val, float):

                display_val = f"{val:.2%}"

            else:

                display_val = val

            cols[i].metric(

                row["Metric"],

                display_val

            )


    st.divider()


    # =========================
    # PORTFOLIO VALUE
    # =========================

    st.subheader("Portfolio Growth")

    fig_growth = px.line(

        df,

        x="Date",

        y="Total_Value"

    )

    st.plotly_chart(
        fig_growth,
        use_container_width=True
    )


    # =========================
    # DAILY RETURNS
    # =========================

    if "Daily_Return" in df.columns:

        st.subheader("Daily Returns")

        fig_returns = px.line(

            df,

            x="Date",

            y="Daily_Return"

        )

        st.plotly_chart(
            fig_returns,
            use_container_width=True
        )


    # =========================
    # ROLLING RETURNS
    # =========================

    rolling_cols = [

        c

        for c in df.columns

        if "Rolling_" in c

    ]

    if rolling_cols:

        st.subheader("Rolling Returns")

        fig_roll = px.line(

            df,

            x="Date",

            y=rolling_cols

        )

        st.plotly_chart(
            fig_roll,
            use_container_width=True
        )


    # =========================
    # DRAWDOWN
    # =========================

    if "Drawdown" in df.columns:

        st.subheader("Drawdown Curve")

        fig_dd = px.line(

            df,

            x="Date",

            y="Drawdown"

        )

        st.plotly_chart(
            fig_dd,
            use_container_width=True
        )


    # =========================
    # RETURN DISTRIBUTION
    # =========================

    if "Daily_Return" in df.columns:

        st.subheader("Return Distribution")

        fig_hist = px.histogram(

            df,

            x="Daily_Return",

            nbins=min(len(df), 100)

        )

        st.plotly_chart(
            fig_hist,
            use_container_width=True
        )


    # =========================
    # TABLE
    # =========================

    st.subheader("Performance Metrics")

    st.dataframe(
        metrics,
        use_container_width=True
    )