from services import parser_rules
import pandas as pd

def test_parse_rules_flat():
    flat = pd.DataFrame({
        "parent_id":["73"]*4,
        "child_id":["73.54","73.55","73.516","73.515"],
        "method":["KVI"]*4,
        "weight":[40,30,20,10],
        "amount":[None]*4,
        "valid_from":[None]*4,
        "valid_to":[None]*4,
    })
    p="tmp_rules.xlsx"; flat.to_excel(p, index=False, sheet_name="rules_flat")
    with open(p,"rb") as f:
        rules, issues = parser_rules.parse_rules_xlsx(f)
    assert not rules.empty
    assert (rules["parent_id"]=="73").all()
