# AI Financial Analysis Dashboard

A GitHub-ready consulting portfolio project that turns small-business financial data into executive KPIs, interactive charts, scenario forecasts, optional AI commentary, and downloadable reports.

## Features

- Fictional sample CSV and Excel data; no client data.
- CSV/Excel uploads and column validation.
- Revenue growth, margins, profit, cash, and runway KPIs.
- Downside, Base, and Upside forecasts for 3–24 months.
- Optional OpenAI commentary through secrets; fully functional without it.
- Excel and HTML report downloads plus automated tests.

## Input columns

Required: `date`, `revenue`, `cogs`, `operating_expenses`, `cash_balance`. Optional: `customers`. Names are case-insensitive and spaces become underscores. Multiple rows in one month are combined; cash uses the final monthly balance while flow metrics are summed.

## Run locally

Install Python 3.11+, then:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -q
streamlit run app.py
```

## Optional AI commentary

Create `.streamlit/secrets.toml` locally (it is ignored by Git):

```toml
OPENAI_API_KEY = "your-key"
```

Never commit keys or confidential client data.

## Publish to GitHub

Create an empty GitHub repository named `ai-financial-analysis-dashboard` without an auto-generated README. Then run:

```bash
git init
git add .
git commit -m "Build AI financial analysis dashboard"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/ai-financial-analysis-dashboard.git
git push -u origin main
```

Repository description: `Interactive Streamlit dashboard for financial KPIs, scenario forecasting, AI commentary, and report exports.`

Suggested topics: `streamlit`, `plotly`, `financial-analysis`, `forecasting`, `python`, `openai`, `small-business`, `consulting-portfolio`.

## Deploy on Streamlit Community Cloud

1. Push the project to GitHub.
2. Open [share.streamlit.io](https://share.streamlit.io), choose **Create app**, and select the repository.
3. Use branch `main` and entry point `app.py`, then deploy.
4. Optional: add `OPENAI_API_KEY = "..."` under **Settings → Secrets** and restart.

## Forecast limitations

The forecast fits a linear trend to up to 12 recent periods. Scenarios adjust revenue and operating expenses; COGS follows its recent revenue ratio. Forecast profit is added to cash as a simplified planning proxy. This portfolio model is for directional planning, not financial advice or a full three-statement forecast.

## License

MIT.
