"""Presentation layer: the Streamlit screens (owner: Anahi).

Run with: streamlit run app.py
This is the only file that imports streamlit (see CONTRACT.md).
This is a stub that shows a title; the real screens come in task A2.
"""

import streamlit as st

from src import analysis, comparison, strategy, validation  # connected in A2

st.set_page_config(page_title="Stock Portfolio Suggestion Engine")
st.title("Stock Portfolio Suggestion Engine")
st.caption("Educational only: this is not financial advice. The screens arrive in task A2.")
