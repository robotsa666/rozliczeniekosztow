from __future__ import annotations
import streamlit as st

def kpi(label: str, value: str | float | int):
    st.metric(label, value)

def render_kpis(kpis: dict):
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: kpi("Suma kosztów [PLN]", f"{kpis.get('sum_costs', 0):,.2f}")
    with c2: kpi("# OPK", kpis.get("opk_count", 0))
    with c3: kpi("# rodziców", kpis.get("parents_count", 0))
    with c4: kpi("# dzieci", kpis.get("children_count", 0))
    with c5: kpi("# alertów", kpis.get("alerts", 0))
