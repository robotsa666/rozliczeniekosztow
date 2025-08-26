from __future__ import annotations
import pandas as pd
from pathlib import Path

def export_xlsx(alloc_df: pd.DataFrame, balances: pd.DataFrame, period: str) -> str:
    outpath = Path(f"export_{period}.xlsx")
    with pd.ExcelWriter(outpath, engine="openpyxl") as writer:
        alloc_df.to_excel(writer, sheet_name="allocations", index=False)
        balances.to_excel(writer, sheet_name="balances", index=False)
    return str(outpath)
