from __future__ import annotations
import pandas as pd
from services.supabase_client import get_client

def upsert_opk(nodes: pd.DataFrame, owner_id: str) -> None:
    data = nodes.copy()
    data["owner_id"] = owner_id
    payload = data.to_dict(orient="records")
    supa = get_client()
    for chunk in _chunks(payload, 1000):
        supa.table("opk_nodes").upsert(chunk, on_conflict="node_id").execute()

def upsert_rules(rules: pd.DataFrame, owner_id: str) -> None:
    data = rules.copy()
    data["owner_id"] = owner_id
    payload = data.to_dict(orient="records")
    supa = get_client()
    for chunk in _chunks(payload, 1000):
        supa.table("allocation_rules").insert(chunk).execute()

def insert_costs(costs: pd.DataFrame, owner_id: str) -> None:
    data = costs.copy()
    data["owner_id"] = owner_id
    payload = data.to_dict(orient="records")
    supa = get_client()
    for chunk in _chunks(payload, 1000):
        supa.table("cost_transactions").insert(chunk).execute()

def insert_allocations(alloc: pd.DataFrame, owner_id: str) -> None:
    data = alloc.copy()
    data["owner_id"] = owner_id
    payload = data.to_dict(orient="records")
    supa = get_client()
    for chunk in _chunks(payload, 1000):
        supa.table("allocations").insert(chunk).execute()

def clear_period(period: str, owner_id: str) -> None:
    supa = get_client()
    supa.table("allocations").delete().eq("owner_id", owner_id).eq("period", period).execute()

def _chunks(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]
