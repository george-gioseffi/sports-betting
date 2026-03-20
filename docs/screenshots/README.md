# Screenshot Capture Guide

Use this checklist to capture portfolio-quality dashboard images after running:

```bash
make seed
make pipeline
make app
```

Windows alternative:

```powershell
.\run.ps1 seed -Matches 280 -Seed 42
.\run.ps1 pipeline
.\run.ps1 app
```

## General Capture Standards
- Use desktop width (recommended: 1440px+).
- Keep sidebar visible when filters add context.
- Prefer light theme for GitHub readability.
- Avoid personal bookmarks or browser clutter in screenshots.
- Export PNG format.

## Required Screenshots

### 1) Overview Dashboard
- **File name:** `overview_dashboard.png`
- **Page:** `Overview`
- **Capture includes:** top KPI strip + monthly net profit chart + league/market comparison.
- **Purpose:** shows portfolio-level health at first glance.

### 2) Strategies Analysis
- **File name:** `strategies_analysis.png`
- **Page:** `Strategy Analysis`
- **Capture includes:** net profit by strategy + CLV vs yield scatter + risk profile table.
- **Purpose:** highlights return quality versus risk posture.

### 3) CLV Analysis
- **File name:** `clv_analysis.png`
- **Page:** `CLV Analysis`
- **Capture includes:** strategy CLV vs yield chart + CLV by market + bookmaker table.
- **Purpose:** demonstrates execution quality diagnostics.

### 4) Bankroll Simulation
- **File name:** `bankroll_simulation.png`
- **Page:** `Bankroll Simulation`
- **Capture includes:** bankroll evolution line chart + drawdown chart + scenario summary.
- **Purpose:** proves scenario analysis and capital trajectory comparison.

### 5) Risk Dashboard
- **File name:** `risk_dashboard.png`
- **Page:** `Risk Governance Panel`
- **Capture includes:** risk score by strategy + drawdown vs stake intensity + alerts table.
- **Purpose:** evidences governance and capital preservation focus.

### 6) Data Quality Dashboard
- **File name:** `data_quality_dashboard.png`
- **Page:** `Data Quality Dashboard`
- **Capture includes:** validation status chart + detailed checks table.
- **Purpose:** reinforces trust in data contracts and pipeline reliability.

## Recommended Capture Order
1. Home
2. Overview
3. Strategy Analysis
4. Market Analysis
5. CLV Analysis
6. Bankroll Simulation
7. Risk Governance Panel
8. Data Quality Dashboard

## Recommended Filter State for Better Prints
- Keep all leagues and markets selected.
- Keep all strategies selected.
- Keep all simulation methods selected.
- Use full date range on first pass.
- For one detail screenshot, apply:
  - Strategy: `Quant_Value`
  - League: `Premier League`
  - Market: `MONEYLINE_HOME`

## Optional Enhancements
- Add `home_snapshot.png` from `Home` page.
- Add one filtered view example with a note like "Premier League + Quant_Value filter".

## README Embedding
After saving images, embed in `README.md`:

```markdown
![Overview](docs/screenshots/overview_dashboard.png)
![Strategies](docs/screenshots/strategies_analysis.png)
![CLV](docs/screenshots/clv_analysis.png)
![Bankroll](docs/screenshots/bankroll_simulation.png)
![Risk](docs/screenshots/risk_dashboard.png)
![Data Quality](docs/screenshots/data_quality_dashboard.png)
```
