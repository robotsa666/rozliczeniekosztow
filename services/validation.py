from __future__ import annotations
import pandas as pd

def validate_all(opk_df: pd.DataFrame, rules_df: pd.DataFrame, costs_df: pd.DataFrame) -> pd.DataFrame:
    issues = []
    if opk_df.empty:
        issues.append({"severity":"ERROR","message":"Brak wczytanego drzewa OPK."})
    if rules_df.empty:
        issues.append({"severity":"ERROR","message":"Brak wczytanych zasad alokacji."})
    if costs_df.empty:
        issues.append({"severity":"WARN","message":"Brak kosztów źródłowych dla okresu."})
    if not opk_df.empty and not rules_df.empty:
        nodes = set(opk_df["node_id"])
        for _, r in rules_df.iterrows():
            if r["parent_id"] not in nodes:
                issues.append({"severity":"ERROR","message":f"Reguła: parent {r['parent_id']} nie istnieje w drzewie."})
            if r["child_id"] not in nodes:
                issues.append({"severity":"ERROR","message":f"Reguła: child {r['child_id']} nie istnieje w drzewie."})
    if not opk_df.empty and not costs_df.empty:
        nodes = set(opk_df["node_id"])
        for _, r in costs_df.iterrows():
            if r["opk_id"] not in nodes:
                issues.append({"severity":"ERROR","message":f"Koszt {r['doc_no']}: OPK {r['opk_id']} spoza drzewa."})
    return pd.DataFrame(issues)
