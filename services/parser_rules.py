from __future__ import annotations
import pandas as pd
from typing import Tuple, List

ALLOWED_METHODS = {"KVI","EQUAL","MANUAL"}

def parse_rules_xlsx(file) -> Tuple[pd.DataFrame, pd.DataFrame]:
    xls = pd.ExcelFile(file)
    issues: List[dict] = []
    rules = pd.DataFrame(columns=["parent_id","child_id","method","weight","amount","valid_from","valid_to"])

    if "rules_flat" in xls.sheet_names:
        flat = pd.read_excel(xls, sheet_name="rules_flat", dtype=str)
        flat = _normalize_flat(flat)
        rules = pd.concat([rules, flat], ignore_index=True)
    else:
        if set(["parent_header","children_table"]).issubset(xls.sheet_names):
            parent = pd.read_excel(xls, sheet_name="parent_header")
            children = pd.read_excel(xls, sheet_name="children_table")
            if not {"Id OPK (rodzic)"}.issubset(parent.columns):
                issues.append({"severity":"ERROR","message":"Brak kolumny 'Id OPK (rodzic)'."})
            parent_id = str(parent.iloc[0]["Id OPK (rodzic)"])
            kids = []
            for _,r in children.iterrows():
                if pd.isna(r.get("Id OPK (dziecko)")): continue
                cid = str(r["Id OPK (dziecko)"])
                w = r.get("KVI", None)
                kids.append({"parent_id": parent_id, "child_id": cid, "method":"KVI", "weight": _to_num(w), "amount": None, "valid_from": None, "valid_to": None})
            rules = pd.DataFrame(kids)
        else:
            sheet0 = pd.read_excel(xls, sheet_name=0)
            if {"Id OPK (dziecko)","KVI"}.issubset(set(sheet0.columns)):
                parent_id = str(sheet0.get("Id OPK (rodzic)", pd.Series([""])).iloc[0]).strip() or "PARENT"
                kids = []
                for _, r in sheet0.iterrows():
                    if pd.isna(r.get("Id OPK (dziecko)")): continue
                    kids.append({"parent_id": parent_id, "child_id": str(r["Id OPK (dziecko)"]), "method": "KVI",
                                 "weight": _to_num(r.get("KVI")), "amount": None, "valid_from": None, "valid_to": None})
                rules = pd.DataFrame(kids)
            else:
                issues.append({"severity":"ERROR","message":"Nie wykryto formatu zasad."})

    v_issues = validate_rules(rules)
    issues.extend(v_issues)
    rules["weight"] = rules["weight"].astype(float).where(rules["weight"].notna(), None)
    rules["amount"] = rules["amount"].astype(float).where(rules["amount"].notna(), None)
    return rules, pd.DataFrame(issues)

def _normalize_flat(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    needed = ["parent_id","child_id","method","weight","amount","valid_from","valid_to"]
    for c in needed:
        if c not in out.columns: out[c] = None
    out["method"] = out["method"].str.upper().fillna("KVI")
    out["weight"] = pd.to_numeric(out["weight"], errors="coerce")
    out["amount"] = pd.to_numeric(out["amount"], errors="coerce")
    return out[needed]

def _to_num(x):
    try: return float(x)
    except Exception: return None

def validate_rules(rules: pd.DataFrame) -> List[dict]:
    issues: List[dict] = []
    if rules.empty:
        issues.append({"severity":"ERROR","message":"Brak reguł alokacji."})
        return issues
    for pid, grp in rules.groupby("parent_id"):
        method_set = set(grp["method"].unique())
        if "KVI" in method_set:
            s = grp.loc[grp["method"]=="KVI","weight"].fillna(0).sum()
            if s <= 0:
                issues.append({"severity":"ERROR","message":f"Parent {pid}: suma KVI <= 0"})
        if "MANUAL" in method_set:
            if grp.loc[grp["method"]=="MANUAL","amount"].isna().any():
                issues.append({"severity":"ERROR","message":f"Parent {pid}: MANUAL bez kwot dla dzieci"})
        if not method_set.issubset(ALLOWED_METHODS):
            issues.append({"severity":"ERROR","message":f"Parent {pid}: niedozwolone metody: {method_set-ALLOWED_METHODS}"})
        if grp.shape[0] < 1:
            issues.append({"severity":"ERROR","message":f"Parent {pid}: brak dzieci"})
    return issues
