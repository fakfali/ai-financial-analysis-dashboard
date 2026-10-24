from __future__ import annotations

import html
import os
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from financial_dashboard.analysis import (
    build_excel_report,
    compute_kpis,
    forecast_financials,
    normalize_financial_data,
)

LOGO = Path("assets/akeali-logo.png")
SCENARIOS = ["Downside", "Base", "Upside"]
COLORS = {"Downside": "#B42318", "Base": "#C79A2B", "Upside": "#16835D"}

st.set_page_config(
    page_title="AI financial analysis | Akeali & Associates",
    page_icon=":material/finance_mode:",
    layout="wide",
)
st.logo(str(LOGO), size="large")
st.image(str(LOGO), width=460, alt="Akeali and Associates logo")
st.title("AI financial analysis dashboard")
st.caption("Executive reporting, scenario planning, and decision support for small businesses")


@st.cache_data
def load_sample() -> pd.DataFrame:
    return pd.read_csv("data/sample_financials.csv")


def money(value: float) -> str:
    return f"${value:,.0f}"


def pct(value: float) -> str:
    return "n.a." if pd.isna(value) else f"{value:.1%}"


def read_upload(uploaded_file) -> pd.DataFrame:
    if uploaded_file.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


def health_label(kpis: dict[str, float]) -> tuple[str, str, str]:
    if kpis["operating_profit"] < 0:
        return "Needs attention", "red", "Operating costs currently exceed gross profit."
    if kpis["revenue_growth"] < 0:
        return "Monitor", "orange", "The business is profitable, but revenue declined in the latest period."
    return "Healthy", "green", "Revenue and operating profit are positive in the latest period."


with st.sidebar:
    st.image(str(LOGO), width="stretch", alt="Akeali and Associates logo")
    st.header("Data and assumptions", icon=":material/tune:")
    uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx", "xls"])
    st.caption("Use the sample company or upload monthly financial data.")

try:
    raw = read_upload(uploaded) if uploaded else load_sample()
    all_actuals = normalize_financial_data(raw)
except Exception as exc:
    st.error(f"Could not load the data: {exc}", icon=":material/error:")
    st.stop()

with st.sidebar:
    min_date = all_actuals["date"].min().date()
    max_date = all_actuals["date"].max().date()
    selected_dates = st.date_input(
        "Analysis period",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    scenario = st.segmented_control("Forecast scenario", SCENARIOS, default="Base") or "Base"
    horizon = st.slider("Forecast horizon (months)", 3, 24, 12)
    show_customers = st.toggle("Show customer analysis", value=True, disabled="customers" not in all_actuals)
    st.download_button(
        "Download CSV template",
        load_sample().head(1).to_csv(index=False),
        "financial_template.csv",
        "text/csv",
        icon=":material/download:",
        width="stretch",
    )

start_date, end_date = selected_dates if len(selected_dates) == 2 else (min_date, max_date)
actuals = all_actuals[
    (all_actuals["date"].dt.date >= start_date) & (all_actuals["date"].dt.date <= end_date)
].copy()
if actuals.empty:
    st.warning("The selected period contains no records.", icon=":material/warning:")
    st.stop()

kpis = compute_kpis(actuals)
forecast = forecast_financials(actuals, horizon, scenario)
status, status_color, status_note = health_label(kpis)

context_left, context_right = st.columns([3, 1], vertical_alignment="center")
with context_left:
    source_name = uploaded.name if uploaded else "Fictional sample company"
    st.caption(f"Source: {source_name} · Period: {start_date:%b %Y} to {end_date:%b %Y} · Scenario: {scenario}")
with context_right:
    st.badge(status, color=status_color, icon=":material/monitoring:")

st.subheader("Executive KPIs")
first_row = st.columns(3)
first_row[0].metric(
    "Monthly revenue",
    money(kpis["revenue"]),
    pct(kpis["revenue_growth"]),
    delta_description="vs. prior period",
    border=True,
    height="stretch",
    chart_data=actuals["revenue"].tail(8),
)
first_row[1].metric(
    "Gross margin",
    pct(kpis["gross_margin"]),
    border=True,
    height="stretch",
    chart_data=actuals["gross_margin"].tail(8),
)
first_row[2].metric(
    "Operating profit",
    money(kpis["operating_profit"]),
    border=True,
    height="stretch",
    chart_data=actuals["operating_profit"].tail(8),
)
second_row = st.columns(3)
second_row[0].metric("Operating margin", pct(kpis["operating_margin"]), border=True, height="stretch")
second_row[1].metric("Cash balance", money(kpis["cash_balance"]), border=True, height="stretch")
second_row[2].metric(
    "Cash runway",
    "Cash-generating" if np.isinf(kpis["runway_months"]) else f"{kpis['runway_months']:.1f} months",
    border=True,
    height="stretch",
)
st.caption(status_note)

overview_tab, forecast_tab, details_tab = st.tabs(
    [":material/dashboard: Performance", ":material/query_stats: Forecast", ":material/table_chart: Data and reports"]
)

with overview_tab:
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            trend = actuals.melt(
                id_vars="date",
                value_vars=["revenue", "gross_profit", "operating_profit"],
                var_name="Metric",
                value_name="Amount",
            )
            performance_fig = px.line(
                trend,
                x="date",
                y="Amount",
                color="Metric",
                markers=True,
                title="Monthly financial performance",
                color_discrete_sequence=["#C79A2B", "#111111", "#16835D"],
            )
            performance_fig.update_layout(yaxis_tickprefix="$", legend_title=None, hovermode="x unified")
            st.plotly_chart(performance_fig, width="stretch", alt="Monthly revenue, gross profit, and operating profit")
    with right:
        with st.container(border=True):
            margins = actuals.melt(
                id_vars="date",
                value_vars=["gross_margin", "operating_margin"],
                var_name="Metric",
                value_name="Margin",
            )
            margin_fig = px.line(
                margins,
                x="date",
                y="Margin",
                color="Metric",
                markers=True,
                title="Profitability margins",
                color_discrete_sequence=["#C79A2B", "#111111"],
            )
            margin_fig.update_layout(yaxis_tickformat=".0%", legend_title=None, hovermode="x unified")
            st.plotly_chart(margin_fig, width="stretch", alt="Gross and operating margins over time")

    cash_col, customer_col = st.columns(2)
    with cash_col:
        with st.container(border=True):
            cash_fig = px.area(actuals, x="date", y="cash_balance", title="Ending cash balance", color_discrete_sequence=["#C79A2B"])
            cash_fig.update_layout(yaxis_tickprefix="$", hovermode="x unified")
            st.plotly_chart(cash_fig, width="stretch", alt="Ending cash balance over time")
    with customer_col:
        with st.container(border=True):
            if show_customers and "customers" in actuals:
                customer_fig = px.line(actuals, x="date", y="customers", markers=True, title="Active customers", color_discrete_sequence=["#111111"])
                st.plotly_chart(customer_fig, width="stretch", alt="Active customers over time")
            else:
                st.subheader("Customer analysis")
                st.caption("Include a `customers` column in uploaded data to enable this view.")

with forecast_tab:
    st.subheader(f"{scenario} scenario forecast")
    scenario_fig = go.Figure()
    scenario_fig.add_scatter(x=actuals["date"], y=actuals["revenue"], name="Actual revenue", line={"color": "#111111"})
    scenario_fig.add_scatter(x=forecast["date"], y=forecast["revenue"], name=f"{scenario} revenue", line={"color": COLORS[scenario], "dash": "dash"})
    scenario_fig.add_scatter(x=forecast["date"], y=forecast["operating_profit"], name="Forecast operating profit", line={"color": "#16835D", "dash": "dot"})
    scenario_fig.update_layout(yaxis_tickprefix="$", hovermode="x unified")
    st.plotly_chart(scenario_fig, width="stretch", alt=f"Actual results and {scenario.lower()} forecast")

    comparisons = pd.concat([forecast_financials(actuals, horizon, name) for name in SCENARIOS], ignore_index=True)
    comparison_fig = px.line(
        comparisons,
        x="date",
        y="revenue",
        color="scenario",
        title="Revenue comparison across scenarios",
        color_discrete_map=COLORS,
    )
    comparison_fig.update_layout(yaxis_tickprefix="$", legend_title=None, hovermode="x unified")
    st.plotly_chart(comparison_fig, width="stretch", alt="Revenue forecasts for downside, base, and upside scenarios")

    end_values = comparisons.groupby("scenario", as_index=False).tail(1)[["scenario", "date", "revenue", "operating_profit", "cash_balance"]]
    st.dataframe(
        end_values,
        hide_index=True,
        width="stretch",
        column_config={
            "scenario": "Scenario",
            "date": st.column_config.DateColumn("Forecast end", format="MMM YYYY"),
            "revenue": st.column_config.NumberColumn("Revenue", format="dollar"),
            "operating_profit": st.column_config.NumberColumn("Operating profit", format="dollar"),
            "cash_balance": st.column_config.NumberColumn("Cash balance", format="dollar"),
        },
        alt="Forecast ending values by scenario",
    )

with details_tab:
    st.subheader("Management commentary")
    commentary = (
        f"Revenue is {pct(kpis['revenue_growth'])} versus the prior period. Gross margin is "
        f"{pct(kpis['gross_margin'])}, and operating profit is {money(kpis['operating_profit'])}. "
        f"Under the {scenario.lower()} scenario, forecast revenue reaches "
        f"{money(float(forecast.iloc[-1]['revenue']))} by {forecast.iloc[-1]['date']:%B %Y}."
    )
    if st.button("Generate optional AI commentary", icon=":material/auto_awesome:"):
        api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY", None)
        if not api_key:
            st.info("Add OPENAI_API_KEY to Streamlit secrets to enable AI commentary. The dashboard works without it.")
        else:
            try:
                from openai import OpenAI

                commentary = OpenAI(api_key=api_key).responses.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
                    input=f"Write three concise CFO bullets using only these facts: {kpis}; scenario {scenario}; ending forecast revenue {float(forecast.iloc[-1]['revenue'])}.",
                ).output_text
            except Exception as exc:
                st.warning(f"AI commentary was unavailable; using the rules-based summary. {exc}")
    st.write(commentary)

    st.subheader("Detailed monthly data")
    st.dataframe(
        actuals,
        hide_index=True,
        width="stretch",
        column_config={
            "date": st.column_config.DateColumn("Month", format="MMM YYYY"),
            "revenue": st.column_config.NumberColumn("Revenue", format="dollar"),
            "cogs": st.column_config.NumberColumn("COGS", format="dollar"),
            "operating_expenses": st.column_config.NumberColumn("Operating expenses", format="dollar"),
            "gross_profit": st.column_config.NumberColumn("Gross profit", format="dollar"),
            "operating_profit": st.column_config.NumberColumn("Operating profit", format="dollar"),
            "gross_margin": st.column_config.NumberColumn("Gross margin", format="percent"),
            "operating_margin": st.column_config.NumberColumn("Operating margin", format="percent"),
        },
        alt="Detailed monthly financial data",
    )

    report = build_excel_report(actuals, forecast, kpis)
    html_report = f"""<!doctype html><html><head><meta charset='utf-8'><title>Akeali financial analysis</title></head>
    <body><h1>Akeali &amp; Associates financial analysis</h1><p>{html.escape(commentary)}</p>
    {pd.DataFrame({'Metric': list(kpis), 'Value': list(kpis.values())}).to_html(index=False)}
    <p>Scenario: {html.escape(scenario)}. Forecast through {forecast.iloc[-1]['date']:%B %Y}.</p></body></html>"""
    download_left, download_right = st.columns(2)
    download_left.download_button(
        "Download Excel report",
        report,
        "akeali_financial_analysis.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        icon=":material/download:",
        width="stretch",
    )
    download_right.download_button(
        "Download HTML report",
        html_report,
        "akeali_financial_analysis.html",
        "text/html",
        icon=":material/download:",
        width="stretch",
    )

st.caption("Forecasts are directional planning estimates based on recent linear trends. They are not financial advice.")
