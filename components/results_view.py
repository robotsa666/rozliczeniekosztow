from __future__ import annotations
import streamlit as st
import pandas as pd

def render_results(alloc_df: pd.DataFrame, balances: pd.DataFrame) -> None:
    if alloc_df is not None and not alloc_df.empty:
        st.write("Dziennik alokacji (źródło → cel):")
        st.dataframe(alloc_df, use_container_width=True, height=300)
    if balances is not None and not balances.empty:
        st.write("Salda końcowe per OPK:")
        st.dataframe(balances, use_container_width=True, height=300)
        st.write("Top 10 kosztów końcowych:")
        topn = balances.nlargest(10, "final_balance")
        st.bar_chart(topn.set_index("opk_id")["final_balance"])
