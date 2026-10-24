from io import BytesIO
import numpy as np
import pandas as pd
REQUIRED=("date","revenue","cogs","operating_expenses","cash_balance")
def normalize_financial_data(df):
 df=df.copy(); df.columns=[str(c).strip().lower().replace(" ","_") for c in df.columns]
 missing=[c for c in REQUIRED if c not in df]
 if missing: raise ValueError("Missing required columns: "+", ".join(missing))
 if df.empty: raise ValueError("The file contains no data rows.")
 df["date"]=pd.to_datetime(df["date"],errors="raise").dt.to_period("M").dt.to_timestamp()
 numeric=[c for c in REQUIRED[1:]+("customers",) if c in df]
 for c in numeric: df[c]=pd.to_numeric(df[c],errors="raise")
 agg={c:"sum" for c in numeric}; agg["cash_balance"]="last"; df=df.groupby("date",as_index=False).agg(agg).sort_values("date")
 df["gross_profit"]=df.revenue-df.cogs; df["operating_profit"]=df.gross_profit-df.operating_expenses
 df["gross_margin"]=np.where(df.revenue!=0,df.gross_profit/df.revenue,np.nan); df["operating_margin"]=np.where(df.revenue!=0,df.operating_profit/df.revenue,np.nan); df["revenue_growth"]=df.revenue.pct_change()
 return df.reset_index(drop=True)
def compute_kpis(df):
 c=df.iloc[-1]; p=df.iloc[-2] if len(df)>1 else c; burn=max(0,-float(df.tail(12).operating_profit.mean()))
 return {"revenue":float(c.revenue),"revenue_growth":float(c.revenue/p.revenue-1) if p.revenue else np.nan,"gross_margin":float(c.gross_margin),"operating_profit":float(c.operating_profit),"operating_margin":float(c.operating_margin),"cash_balance":float(c.cash_balance),"runway_months":float(c.cash_balance/burn) if burn else np.inf}
def forecast_financials(df,months,scenario="Base"):
 if not 1<=months<=36: raise ValueError("Forecast horizon must be between 1 and 36 months.")
 adj={"Downside":(-.2,.05),"Base":(0,0),"Upside":(.2,-.03)}
 if scenario not in adj: raise ValueError("Unknown scenario: "+scenario)
 h=df.tail(min(12,len(df))); x=np.arange(len(h)); future=np.arange(len(h),len(h)+months)
 def trend(c):
  v=h[c].to_numpy(float); return np.repeat(v[0],months) if len(v)==1 else np.polyval(np.polyfit(x,v,1),future)
 ra,ea=adj[scenario]; revenue=np.maximum(0,trend("revenue")*(1+ra)); cogs=revenue*(h.cogs.sum()/h.revenue.sum() if h.revenue.sum() else 0); opex=np.maximum(0,trend("operating_expenses")*(1+ea)); profit=revenue-cogs-opex
 cash=[]; running=float(df.iloc[-1].cash_balance)
 for p in profit: running+=float(p); cash.append(running)
 out=pd.DataFrame({"date":pd.date_range(df.date.max()+pd.offsets.MonthBegin(1),periods=months,freq="MS"),"revenue":revenue,"cogs":cogs,"operating_expenses":opex,"operating_profit":profit,"cash_balance":cash,"scenario":scenario})
 out["gross_profit"]=out.revenue-out.cogs; out["gross_margin"]=out.gross_profit/out.revenue; out["operating_margin"]=out.operating_profit/out.revenue; return out
def build_excel_report(actuals,forecast,kpis):
 output=BytesIO()
 with pd.ExcelWriter(output,engine="xlsxwriter",datetime_format="mmm-yy") as writer:
  pd.DataFrame({"Metric":list(kpis),"Value":list(kpis.values())}).to_excel(writer,sheet_name="Executive Summary",index=False); actuals.to_excel(writer,sheet_name="Actuals",index=False); forecast.to_excel(writer,sheet_name="Forecast",index=False)
  for name,frame in (("Actuals",actuals),("Forecast",forecast)):
   ws=writer.sheets[name]; ws.freeze_panes(1,1); ws.set_column(0,len(frame.columns)-1,18)
 return output.getvalue()

