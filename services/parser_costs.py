from __future__ import annotations
import pandas as pd
from typing import Tuple, List
import unicodedata, re

def _normalize_header(h: str) -> str:
    h = "".join(c for c in unicodedata.normalize("NFKD", h) if not unicodedata.combining(c))
    h = h.lower()
    h = re.sub(r"\s+", " ", h)
    return h.strip()

def parse_costs_xlsx(file, fallback_period: str | None = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    raw = pd.read_excel(file, sheet_name=0)
    rename = {c: _normalize_header(c) for c in raw.columns}
    df = raw.rename(columns=rename)

    col_map = {
        "doc_no": ["numer dokumentu","nr dokumentu","dokument"],
        "doc_date": ["data otrzymania","data","data dokumentu"],
        "name": ["nazwa","opis","tytul"],
        "amount": ["cena netto [pln]","kwota","netto"],
        "opk_id": ["id opk","opk","opk id","id"]
    }
    out = pd.DataFrame()
    for target, candidates in col_map.items():
        for c in candidates:
            if c in df.columns:
                out[target] = df[c]; break
        if target not in out.columns:
            out[target] = None

    out["amount"] = pd.to_numeric(out["amount"], errors="coerce")
    out["doc_date"] = pd.to_datetime(out["doc_date"], errors="coerce").dt.date
    out["doc_no"] = out["doc_no"].astype(str)
    out["name"] = out["name"].astype(str)
    out["opk_id"] = out["opk_id"].astype(str)

    if fallback_period:
        out["period"] = fallback_period
    else:
        out["period"] = out["doc_date"].apply(lambda d: f"{d.year}-{d.month:02d}" if pd.notna(d) else None)

    issues: List[dict] = []
    if out["opk_id"].isna().any() or (out["opk_id"] == "" ).any():
        issues.append({"severity":"ERROR","message":"Puste ID OPK w kosztach."})
    if out["amount"].isna().any():
        issues.append({"severity":"ERROR","message":"Nieparsowalne kwoty."})
    if out["doc_date"].isna().any():
        issues.append({"severity":"ERROR","message":"Nieparsowalne daty dokumentów."})
    if (out["amount"] < 0).any():
        issues.append({"severity":"INFO","message":"Ujemne kwoty (korekty) – ujęto."})

    out = out[["doc_no","doc_date","period","name","opk_id","amount"]].copy()
    return out, pd.DataFrame(issues)
