import pandas as pd
from services import allocation

def test_allocation_kvi_100k():
    opk_df = pd.DataFrame({
        "node_id": ["73","73.54","73.55","73.516","73.515"],
        "parent_id": [None,"73","73","73","73"],
        "level": [1,2,2,2,2],
        "name": ["MO","54","55","516","515"],
        "path_labels": [["MO"],["MO","54"],["MO","55"],["MO","516"],["MO","515"]],
    })
    rules_df = pd.DataFrame({
        "parent_id":["73"]*4,
        "child_id":["73.54","73.55","73.516","73.515"],
        "method":["KVI","KVI","KVI","KVI"],
        "weight":[40,30,20,10],
        "amount":[None,None,None,None],
        "valid_from":[None,None,None,None],
        "valid_to":[None,None,None,None],
    })
    costs_df = pd.DataFrame({
        "doc_no":["X"],
        "doc_date":[pd.Timestamp("2025-07-01").date()],
        "period":["2025-07"],
        "name":["Test"],
        "opk_id":["73"],
        "amount":[100000.00]
    })
    alloc_df, balances = allocation.allocate("2025-07", opk_df, rules_df, costs_df, mode="single-pass")
    assert round(alloc_df["amount"].sum(), 2) == 100000.00
    exp = {"73.54":40000.0,"73.55":30000.0,"73.516":20000.0,"73.515":10000.0}
    got = dict(zip(alloc_df["target_opk"], alloc_df["amount"]))
    for k,v in exp.items():
        assert round(got[k],2) == v
