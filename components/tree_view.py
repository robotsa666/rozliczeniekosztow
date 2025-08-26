from __future__ import annotations
import streamlit as st
import pandas as pd

def _children_of(df: pd.DataFrame, parent_id: str | None) -> list[str]:
    return df.loc[df["parent_id"].fillna("") == (parent_id or ""), "node_id"].tolist()

def _name_of(df: pd.DataFrame, node_id: str) -> str:
    row = df.loc[df["node_id"] == node_id].iloc[0]
    return f"{node_id} · {row['name']}"

def render_tree(opk_df: pd.DataFrame) -> None:
    roots = opk_df.loc[opk_df["parent_id"].isna(), "node_id"].tolist()
    for r in roots:
        with st.expander(_name_of(opk_df, r), expanded=False):
            _render_subtree(opk_df, r, level=1)

def _render_subtree(opk_df: pd.DataFrame, parent: str, level: int) -> None:
    children = _children_of(opk_df, parent)
    for c in children:
        with st.expander("— " * level + _name_of(opk_df, c), expanded=False):
            _render_subtree(opk_df, c, level+1)
