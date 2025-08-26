from __future__ import annotations
import streamlit as st
import pandas as pd

EDITABLE_COLS = ["method", "weight", "amount", "valid_from", "valid_to"]

def rules_editor(rules_df: pd.DataFrame) -> pd.DataFrame:
    st.caption("Edycja działa tymczasowo (zapis do DB osobno).")
    edited = st.data_editor(
        rules_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "method": st.column_config.SelectboxColumn("method", options=["KVI","EQUAL","MANUAL"])
        }
    )
    return edited
