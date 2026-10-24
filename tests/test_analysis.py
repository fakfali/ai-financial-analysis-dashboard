import pandas as pd
import pytest
from financial_dashboard.analysis import *
def sample(): return pd.DataFrame({"date":["2026-01-01","2026-02-01","2026-03-01"],"revenue":[100,110,121],"cogs":[40,44,48.4],"operating_expenses":[50,52,54],"cash_balance":[200,214,232.6]})
def test_metrics():
 d=normalize_financial_data(sample()); assert d.iloc[-1].operating_profit==pytest.approx(18.6); assert compute_kpis(d)["revenue_growth"]==pytest.approx(.1)
def test_forecast():
 f=forecast_financials(normalize_financial_data(sample()),6,"Upside"); assert len(f)==6; assert f.date.min()==pd.Timestamp("2026-04-01")
def test_missing_columns():
 with pytest.raises(ValueError,match="Missing required columns"): normalize_financial_data(pd.DataFrame({"date":["2026-01-01"]}))
def test_bad_scenario():
 with pytest.raises(ValueError,match="Unknown scenario"): forecast_financials(normalize_financial_data(sample()),6,"Extreme")
