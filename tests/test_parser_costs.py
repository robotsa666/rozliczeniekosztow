from services import parser_costs
import pandas as pd
from datetime import date

def test_parse_costs_sample():
    df = pd.DataFrame({
        "Numer dokumentu":["FV/001"],
        "Data otrzymania":[date(2025,7,5)],
        "Nazwa":["Test"],
        "Cena netto [PLN]":[100.0],
        "ID OPK":["73"]
    })
    p="tmp_costs.xlsx"; df.to_excel(p, index=False)
    with open(p,"rb") as f:
        out, issues = parser_costs.parse_costs_xlsx(f, fallback_period="2025-07")
    assert not out.empty
    assert (out["period"]=="2025-07").all()
