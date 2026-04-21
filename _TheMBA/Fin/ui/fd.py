import streamlit as st
import plotly.express as px



def render_fd_page(system):

    st.title("Fixed Deposit Analytics")

    fd_data = system.get("fd", {})

    if not fd_data:

        st.warning("No FD data available")

        return


    df = fd_data["fd_df"]


    # =====================================
    # KPIs
    # =====================================

    k1, k2, k3, k4 = st.columns(4)

    k1.metric(

        "Total FD Value",

        f"₹{fd_data['total_value']:,.0f}"

    )

    k2.metric(

        "Weighted Rate",

        f"{fd_data['weighted_rate']:.2f}%"

    )

    k3.metric(

        "Avg Tenure Remaining",

        f"{fd_data['weighted_tenure']:.2f} Years"

    )

    k4.metric(

        "Number of FDs",

        len(df)

    )


    st.divider()


    # =====================================
    # MATURITY LADDER
    # =====================================

    st.subheader("Maturity Ladder")


    fig_maturity = px.bar(

        fd_data["maturity_dist"],

        x="Maturity_Bucket",

        y="Principal_Amount"

    )


    st.plotly_chart(

        fig_maturity,

        width="stretch"

    )


    # =====================================
    # BANK EXPOSURE
    # =====================================

    if not fd_data["bank_dist"].empty:

        st.subheader("Bank Exposure")


        fig_bank = px.pie(

            fd_data["bank_dist"],

            values="Principal_Amount",

            names="Bank_Post_Office"

        )


        st.plotly_chart(

            fig_bank,

            width="stretch"

        )


    # =====================================
    # INTEREST RATE DISTRIBUTION
    # =====================================

    if "Interest_Rate_Pct" in df.columns:

        st.subheader("Interest Rate Distribution")


        fig_rate = px.histogram(

            df,

            x="Interest_Rate_Pct",

            nbins=20

        )


        st.plotly_chart(

            fig_rate,

            width="stretch"

        )


    # =====================================
    # MATURITY TIMELINE
    # =====================================

    if "Maturity_Date" in df.columns:

        st.subheader("Maturity Timeline")


        fig_time = px.scatter(

            df,

            x="Maturity_Date",

            y="Principal_Amount"

        )


        st.plotly_chart(

            fig_time,

            width="stretch"

        )


    st.divider()


    # =====================================
    # FD TABLE
    # =====================================

    st.subheader("FD Details")

    st.dataframe(

        df,

        width="stretch"

    )