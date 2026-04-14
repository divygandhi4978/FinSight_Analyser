import streamlit as st
from industry import show_industry_overview

st.set_page_config(
    page_title="Healthcare Intelligence",
    layout="wide"
)

tabs = st.tabs(["Industry Overview"])

with tabs[0]:

    show_industry_overview()