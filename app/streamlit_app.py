from __future__ import annotations
import streamlit as st
import pandas as pd
from datetime import date
from services.supabase_client import get_client, get_user
from services import parser_tree, parser_rules, parser_costs, validation, allocation, queries
from exporters import csv_export, xlsx_export
from components.kpi_cards import render_kpis
from components.tree_view import render_tree
from components.upload_box import upload_box
from components.rules_editor import rules_editor
from components.results_view import render_results

st.set_page_config(page_title="Kontroling – OPK & Rozliczenia", layout="wide")

# Sidebar – Auth
st.sidebar.header("Logowanie (Supabase)")
email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Hasło", type="password")
login_col1, login_col2 = st.sidebar.columns([1,1])
if login_col1.button("Zaloguj"):
    supa = get_client()
    try:
        supa.auth.sign_in_with_password({"email": email, "password": password})
        st.sidebar.success("Zalogowano.")
    except Exception as e:
        st.sidebar.error(f"Logowanie nieudane: {e}")

if login_col2.button("Wyloguj"):
    supa = get_client()
    supa.auth.sign_out()
    st.sidebar.info("Wylogowano.")

user = get_user()
if not user:
    st.warning("Zaloguj się, aby korzystać z bazy (RLS). Mimo to możesz testować parsery lokalnie.")
owner_id = user.id if user else None

# Sidebar – Period & Uploads
st.sidebar.header("Parametry")
default_period = st.secrets.get("DEFAULT_PERIOD", f"{date.today().year}-{date.today().month:02d}")
period = st.sidebar.text_input("Okres (YYYY-MM)", value=default_period)

st.sidebar.header("Import XLSX")
tree_file = upload_box("Drzewo OPK (XLSX)")
rules_file = upload_box("Zasady rozliczeń (XLSX)")
costs_file = upload_box("Koszty źródłowe (XLSX)")

act_col1, act_col2, act_col3, act_col4 = st.sidebar.columns(4)
btn_validate = act_col1.button("Waliduj")
btn_run = act_col2.button("Uruchom alokację")
btn_clear = act_col3.button("Wyczyść okres")
btn_export = act_col4.button("Eksport")

st.title("Kontroling – OPK & Rozliczenia")

# State
if "validation_log" not in st.session_state:
    st.session_state["validation_log"] = pd.DataFrame(columns=["severity","message"])
if "alloc_df" not in st.session_state:
    st.session_state["alloc_df"] = pd.DataFrame()
if "balances" not in st.session_state:
    st.session_state["balances"] = pd.DataFrame()

# Parse uploads
opk_df = pd.DataFrame()
rules_df = pd.DataFrame()
costs_df = pd.DataFrame()

if tree_file is not None:
    opk_df, tree_issues = parser_tree.parse_tree_xlsx(tree_file)
    st.session_state["validation_log"] = pd.concat([st.session_state["validation_log"], tree_issues], ignore_index=True)

if rules_file is not None:
    rules_df, rules_issues = parser_rules.parse_rules_xlsx(rules_file)
    st.session_state["validation_log"] = pd.concat([st.session_state["validation_log"], rules_issues], ignore_index=True)

if costs_file is not None:
    costs_df, costs_issues = parser_costs.parse_costs_xlsx(costs_file, fallback_period=period)
    st.session_state["validation_log"] = pd.concat([st.session_state["validation_log"], costs_issues], ignore_index=True)

# KPI
kpis = {
    "sum_costs": float(costs_df["amount"].sum()) if not costs_df.empty else 0.0,
    "opk_count": int(opk_df.shape[0]) if not opk_df.empty else 0,
    "parents_count": int(rules_df["parent_id"].nunique()) if not rules_df.empty else 0,
    "children_count": int(rules_df.shape[0]) if not rules_df.empty else 0,
    "alerts": int((st.session_state["validation_log"]["severity"] == "ERROR").sum())
}
render_kpis(kpis)

col_tree, col_rules = st.columns([1,1])
with col_tree:
    st.subheader("Drzewo OPK")
    if opk_df.empty:
        st.info("Wgraj plik drzewa.")
    else:
        render_tree(opk_df)

with col_rules:
    st.subheader("Zasady rozliczeń")
    if rules_df.empty:
        st.info("Wgraj plik zasad.")
    else:
        rules_df = rules_editor(rules_df)

st.subheader("Koszty źródłowe")
st.dataframe(costs_df, use_container_width=True)

# Actions
if btn_validate:
    issues = validation.validate_all(opk_df, rules_df, costs_df)
    st.session_state["validation_log"] = pd.concat([st.session_state["validation_log"], issues], ignore_index=True)
    st.success("Walidacja zakończona.")

if btn_run:
    if period.strip() == "":
        st.error("Podaj okres (YYYY-MM).")
    else:
        alloc_df, balances = allocation.allocate(
            period=period,
            opk_df=opk_df,
            rules_df=rules_df,
            costs_df=costs_df,
            mode="single-pass"
        )
        st.session_state["alloc_df"] = alloc_df
        st.session_state["balances"] = balances
        st.success("Alokacja zakończona.")

if btn_clear:
    if owner_id:
        queries.clear_period(period, owner_id)
        st.success(f"Wyczyszczono zapis alokacji i koszty dla okresu {period}.")
    else:
        st.info("Brak zalogowanego użytkownika – czyszczenie DB pominięte.")

if btn_export:
    if st.session_state["alloc_df"].empty:
        st.warning("Najpierw uruchom alokację.")
    else:
        csv_paths = csv_export.export_all(st.session_state["alloc_df"], st.session_state["balances"], period)
        xlsx_path = xlsx_export.export_xlsx(st.session_state["alloc_df"], st.session_state["balances"], period)
        st.success("Wyeksportowano.")
        st.write("CSV:")
        for p in csv_paths: st.write(f"- {p}")
        st.write("XLSX:"); st.write(xlsx_path)

# Results & Audit
st.subheader("Wynik alokacji i salda")
render_results(st.session_state["alloc_df"], st.session_state["balances"])

st.subheader("Audyt / Walidacje")
st.dataframe(st.session_state["validation_log"], use_container_width=True)
