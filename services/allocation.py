from __future__ import annotations
import pandas as pd
from typing import Tuple, Dict, List

TOL = 0.01

def _bankers_round(x: float) -> float:
    return float(round(x, 2))

def _adjust_rounding(shares: List[float], base: float, amounts: List[float]) -> List[float]:
    s = sum(amounts)
    diff = _bankers_round(base - s)
    if abs(diff) >= 0.005:
        amounts[-1] = _bankers_round(amounts[-1] + diff)
    return amounts

def _active_rules_for_period(rules_df: pd.DataFrame, period: str) -> pd.DataFrame:
    if rules_df[["valid_from","valid_to"]].isna().all().all():
        return rules_df.copy()
    date_key = pd.Period(period).to_timestamp()
    mask = (
        (rules_df["valid_from"].isna() | (pd.to_datetime(rules_df["valid_from"]) <= date_key)) &
        (rules_df["valid_to"].isna() | (pd.to_datetime(rules_df["valid_to"]) >= date_key))
    )
    return rules_df.loc[mask].copy()

def aggregate_sources(period: str, costs_df: pd.DataFrame) -> pd.DataFrame:
    cur = costs_df.loc[costs_df["period"] == period].copy()
    agg = cur.groupby("opk_id", as_index=False)["amount"].sum().rename(columns={"opk_id":"parent_id","amount":"base_amount"})
    return agg

def _shares_for_parent(grp: pd.DataFrame) -> pd.Series:
    method = grp["method"].iloc[0]
    if method == "KVI":
        s = grp["weight"].fillna(0).sum()
        if s <= 0:
            raise ValueError(f"Suma wag KVI <= 0 dla parent {grp['parent_id'].iloc[0]}")
        return grp["weight"] / s
    elif method == "EQUAL":
        n = len(grp)
        return pd.Series([1.0/n] * n, index=grp.index)
    elif method == "MANUAL":
        s = grp["amount"].fillna(0).sum()
        if s <= 0:
            raise ValueError(f"Suma kwot MANUAL <= 0 dla parent {grp['parent_id'].iloc[0]}")
        return grp["amount"] / s
    else:
        raise ValueError(f"Nieznana metoda: {method}")

def allocate(period: str, opk_df: pd.DataFrame, rules_df: pd.DataFrame, costs_df: pd.DataFrame,
             mode: str = "single-pass") -> Tuple[pd.DataFrame, pd.DataFrame]:
    rules = _active_rules_for_period(rules_df, period)
    base = aggregate_sources(period, costs_df)
    inflow: Dict[str, float] = {}
    out_records: List[dict] = []

    parent_groups = rules.groupby("parent_id")

    def process_parent(pid: str, base_amount: float):
        if base_amount == 0: return
        g = rules[rules["parent_id"] == pid].copy()
        allocs = []
        for m, sub in g.groupby("method"):
            shares = _shares_for_parent(sub)
            amts = [ _bankers_round(base_amount * sh) for sh in shares.tolist() ]
            amts = _adjust_rounding(shares.tolist(), base_amount, amts)
            sub = sub.copy()
            sub["share"] = shares
            sub["alloc_amount"] = amts
            sub["method_used"] = m
            allocs.append(sub)
        merged = pd.concat(allocs, ignore_index=True)
        for _, r in merged.iterrows():
            out_records.append({
                "period": period,
                "source_opk": pid,
                "target_opk": r["child_id"],
                "method": r["method_used"],
                "base_amount": _bankers_round(base_amount),
                "share": float(r["share"]),
                "amount": float(r["alloc_amount"]),
                "rule_id": None
            })
            inflow[r["child_id"]] = inflow.get(r["child_id"], 0.0) + float(r["alloc_amount"])

    if mode == "single-pass":
        for _, row in base.iterrows():
            pid = row["parent_id"]
            if pid not in parent_groups.groups: continue
            process_parent(pid, float(row["base_amount"]))
    else:
        processed: set[str] = set()
        queue = list(base["parent_id"].unique())
        seen = set(queue)
        iter_guard = 0
        while queue and iter_guard < 10000:
            iter_guard += 1
            pid = queue.pop(0)
            processed.add(pid)
            base_amount = float(base.loc[base["parent_id"] == pid, "base_amount"].sum()) + inflow.get(pid, 0.0)
            if pid in parent_groups.groups:
                process_parent(pid, base_amount)
                children = rules.loc[rules["parent_id"] == pid, "child_id"].unique().tolist()
                for c in children:
                    if c in parent_groups.groups and c not in seen:
                        queue.append(c); seen.add(c)

    alloc_df = pd.DataFrame(out_records)
    own = costs_df.loc[costs_df["period"] == period].groupby("opk_id", as_index=False)["amount"].sum().rename(columns={"opk_id":"opk_id","amount":"own_costs"})
    rec = alloc_df.groupby("target_opk", as_index=False)["amount"].sum().rename(columns={"target_opk":"opk_id","amount":"received"})
    sent = alloc_df.groupby("source_opk", as_index=False)["amount"].sum().rename(columns={"source_opk":"opk_id","amount":"sent"})
    balances = pd.merge(own, rec, on="opk_id", how="outer").merge(sent, on="opk_id", how="outer").fillna(0.0)
    balances["final_balance"] = balances["own_costs"] + balances["received"] - balances["sent"]
    alloc_df = alloc_df[["period","source_opk","target_opk","method","base_amount","share","amount","rule_id"]]
    balances = balances[["opk_id","own_costs","received","sent","final_balance"]]
    return alloc_df, balances
