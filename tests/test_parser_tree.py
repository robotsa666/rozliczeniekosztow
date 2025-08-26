import pandas as pd
from services import parser_tree

def test_parse_tree_sample():
    df = pd.DataFrame({
        "Drzewo": ["73","73.54"],
        "OPK1": ["MO","MO"],
        "OPK2": ["","54"],
    })
    p = "tmp_tree.xlsx"; df.to_excel(p, index=False)
    with open(p, "rb") as f:
        nodes, issues = parser_tree.parse_tree_xlsx(f)
    assert not nodes.empty
    assert "node_id" in nodes.columns
    assert (nodes["node_id"] == "73").any()
