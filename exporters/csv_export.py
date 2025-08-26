from __future__ import annotations
import pandas as pd
from pathlib import Path

def export_all(alloc_df: pd.DataFrame, balances: pd.DataFrame, period: str) -> list[str]:
    outdir = Path(f"export_{period}")
    outdir.mkdir(exist_ok=True)
    p1 = outdir / "allocations.csv"
    p2 = outdir / "balances.csv"
    alloc_df.to_csv(p1, index=False)
    balances.to_csv(p2, index=False)
    return [str(p1), str(p2)]
