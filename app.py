import html, os
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from financial_dashboard.analysis import build_excel_report,compute_kpis,forecast_financials,normalize_financial_data
st.set_page_config(page_title="AI Financial Analysis Dashboard",page_icon="📊",layout="wide")
st.title("AI Financial Analysis Dashboard"); st.caption("Executive reporting, monthly trends, and scenario forecasts for small businesses")
@st.cache_data
def sample(): return pd.read_csv("data/sample_financials.csv")
def money(v): return f"${v:,.0f}"
def pct(v): return "n.a." if pd.isna(v) else f"{v:.1%}"
with st.sidebar:
 st.header("Data and forecast"); uploaded=st.file_uploader("Upload CSV or Excel",type=["csv","xlsx","xls"]); scenario=st.selectbox("Scenario",["Downside","Base","Upside"],index=1); horizon=st.slider("Forecast months",3,24,12); st.download_button("Download CSV template",sample().head(1).to_csv(index=False),"financial_template.csv","text/csv")
try:
 raw=(pd.read_csv(uploaded) if uploaded and uploaded.name.lower().endswith(".csv") else pd.read_excel(uploaded)) if uploaded else sample(); actuals=normalize_financial_data(raw)
except Exception as e: st.error(f"Could not load the data: {e}"); st.stop()
k=compute_kpis(actuals); forecast=forecast_financials(actuals,horizon,scenario)
st.subheader("Executive KPIs")

# Two rows of three bordered cards keep every value readable on laptops and tablets.
first_row = st.columns(3)
first_row[0].metric("Monthly revenue", money(k["revenue"]), pct(k["revenue_growth"]), delta_description="vs. prior period", border=True, height="stretch")
first_row[1].metric("Gross margin", pct(k["gross_margin"]), border=True, height="stretch")
first_row[2].metric("Operating profit", money(k["operating_profit"]), border=True, height="stretch")

second_row = st.columns(3)
second_row[0].metric("Operating margin", pct(k["operating_margin"]), border=True, height="stretch")
second_row[1].metric("Cash balance", money(k["cash_balance"]), border=True, height="stretch")
second_row[2].metric("Cash runway", "Cash-generating" if np.isinf(k["runway_months"]) else f"{k['runway_months']:.1f} months", border=True, height="stretch")
left,right=st.columns(2)
with left:
 long=actuals.melt("date",value_vars=["revenue","gross_profit","operating_profit"],var_name="Metric",value_name="Amount"); st.plotly_chart(px.line(long,x="date",y="Amount",color="Metric",markers=True,title="Monthly performance"),width="stretch")
with right:
 margins=actuals.melt("date",value_vars=["gross_margin","operating_margin"],var_name="Metric",value_name="Margin"); fig=px.line(margins,x="date",y="Margin",color="Metric",markers=True,title="Profitability margins"); fig.update_layout(yaxis_tickformat=".0%"); st.plotly_chart(fig,width="stretch")
st.subheader(f"{scenario} scenario forecast"); fig=go.Figure(); fig.add_scatter(x=actuals.date,y=actuals.revenue,name="Actual revenue"); fig.add_scatter(x=forecast.date,y=forecast.revenue,name=f"{scenario} revenue",line={"dash":"dash"}); fig.add_scatter(x=forecast.date,y=forecast.operating_profit,name="Forecast operating profit",line={"dash":"dot"}); st.plotly_chart(fig,width="stretch")
commentary=f"Revenue is {pct(k['revenue_growth'])} versus the prior month. Gross margin is {pct(k['gross_margin'])}, and operating profit is {money(k['operating_profit'])}. Under the {scenario.lower()} scenario, forecast revenue reaches {money(float(forecast.iloc[-1].revenue))} by {forecast.iloc[-1].date:%B %Y}."
st.subheader("Management commentary")
if st.button("Generate optional AI commentary"):
 key=os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY",None)
 if not key: st.info("Add OPENAI_API_KEY to Streamlit secrets. The dashboard works without it.")
 else:
  try:
   from openai import OpenAI
   commentary=OpenAI(api_key=key).responses.create(model=os.getenv("OPENAI_MODEL","gpt-4.1-mini"),input=f"Write 3 concise CFO bullets using only these facts: {k}; scenario {scenario}; ending revenue {float(forecast.iloc[-1].revenue)}").output_text
  except Exception as e: st.warning(f"AI commentary unavailable; using rules-based summary. {e}")
st.write(commentary); report=build_excel_report(actuals,forecast,k); html_report=f"<html><body><h1>Financial Analysis Report</h1><p>{html.escape(commentary)}</p>{pd.DataFrame({'Metric':list(k),'Value':list(k.values())}).to_html(index=False)}</body></html>"; a,b=st.columns(2); a.download_button("Download Excel report",report,"financial_analysis_report.xlsx"); b.download_button("Download HTML report",html_report,"financial_analysis_report.html")
with st.expander("View detailed data"): st.dataframe(actuals,width="stretch")
st.caption("Forecasts are directional estimates based on recent linear trends. They are not financial advice.")
