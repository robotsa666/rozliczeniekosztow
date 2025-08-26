from __future__ import annotations
import pandas as pd
from typing import Tuple

def parse_tree_xlsx(file) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.read_excel(file, sheet_name=0, dtype=str).fillna("")
    cols = df.columns.tolist()
    if "Drzewo" not in cols:
        raise ValueError("Brak kolumny 'Drzewo'.")
    opk_cols = [c for c in cols if c.startswith("OPK")]
    if not opk_cols:
        raise ValueError("Brak kolumn OPK1..OPKk.")
    records = []
    for _, row in df.iterrows():
        node_id = str(row["Drzewo"]).strip()
        if node_id == "":
            continue
        parts = node_id.split(".")
        level = len([p for p in parts if p != ""])
        parent_id = ".".join(parts[:-1]) if level > 1 else None
        labels = [str(row[c]).strip() for c in opk_cols if str(row[c]).strip() != ""]
        name = labels[-1] if labels else node_id
        records.append({"node_id": node_id,"parent_id": parent_id,"level": level,"name": name,"path_labels": labels})
    nodes = pd.DataFrame.from_records(records)
    issues = validate_tree(nodes)
    return nodes, issues

def validate_tree(nodes: pd.DataFrame) -> pd.DataFrame:
    issues = []
    dup = nodes[nodes.duplicated("node_id", keep=False)]
    for nid in dup["node_id"].unique():
        issues.append({"severity":"ERROR","message":f"Duplikat node_id: {nid}"})
    have_parent = nodes[nodes["parent_id"].notna()]
    parents_set = set(nodes["node_id"])
    for _, r in have_parent.iterrows():
        if r["parent_id"] not in parents_set:
            issues.append({"severity":"ERROR","message":f"Sierota: {r['node_id']} (brak rodzica {r['parent_id']})"})
    for nid in nodes["node_id"]:
        seen = set()
        cur = nid
        while True:
            row = nodes[nodes["node_id"] == cur]
            if row.empty: break
            p = row.iloc[0]["parent_id"]
            if p is None or p == "": break
            if p in seen:
                issues.append({"severity":"ERROR","message":f"Wykryto cykl przy {nid} → {p}"}); break
            seen.add(p); cur = p
    for _, r in nodes.iterrows():
        labels = r["path_labels"]
        if isinstance(labels, list) and labels:
            last = labels[-1]
            if str(r["name"]).strip() != str(last).strip():
                issues.append({"severity":"WARN","message":f"Niespójność nazw dla {r['node_id']}: name='{r['name']}' vs last='{last}'"})
    return pd.DataFrame(issues)
