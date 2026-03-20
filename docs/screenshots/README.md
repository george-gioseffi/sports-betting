# Final Screenshot Playbook

Use this guide after running:

```powershell
.\run.ps1 seed -Matches 280 -Seed 42
.\run.ps1 pipeline
.\run.ps1 app
```

## Global Capture Setup
- Resolution: 1440p or higher.
- Theme: light.
- Browser zoom: 100%.
- Keep sidebar visible when filter context adds value.
- Use PNG.

## Recommended Filter States

### State A (Executive)
- Strategies: all
- Leagues: all
- Markets: all
- Simulation Methods: all
- Date Range: full

### State B (Focused)
- Strategy: `Quant_Value`
- League: `Premier League`
- Market: `Home Win`
- Simulation Methods: all
- Date Range: full

## Page-by-Page Screenshots

### 1) Home
- **Screenshot name:** `home-hero.png`
- **Why it matters:** introduces product purpose and top risk context.
- **Best filter state:** State A.
- **Best crop:** page header + KPI strip + workflow block.
- **Recommended use:** LinkedIn + README.

### 2) Overview
- **Screenshot name:** `overview-dashboard.png`
- **Why it matters:** shows portfolio health and ranking at a glance.
- **Best filter state:** State A.
- **Best crop:** KPI strip + monthly chart + league/market ranking tables.
- **Recommended use:** README + LinkedIn.

### 3) Strategies
- **Screenshot name:** `strategy-performance.png`
- **Why it matters:** strongest page to show return-quality vs risk trade-off.
- **Best filter state:** State A.
- **Best crop:** net profit bar + CLV vs yield scatter + scorecard table.
- **Recommended use:** both.

### 4) Markets
- **Screenshot name:** `market-performance.png`
- **Why it matters:** proves segmentation logic by market family.
- **Best filter state:** State A.
- **Best crop:** net profit by market chart + compact table.
- **Recommended use:** README.

### 5) CLV
- **Screenshot name:** `clv-analysis.png`
- **Why it matters:** evidences execution-quality diagnostics.
- **Best filter state:** State A first, State B as optional extra.
- **Best crop:** strategy CLV vs yield scatter + bookmaker summary table.
- **Recommended use:** both.

### 6) Bankroll
- **Screenshot name:** `bankroll-scenarios.png`
- **Why it matters:** shows scenario analysis and survivability impact.
- **Best filter state:** State A.
- **Best crop:** bankroll curve + drawdown curve + scenario table.
- **Recommended use:** both.

### 7) Risk
- **Screenshot name:** `risk-governance.png`
- **Why it matters:** governance focus and risk discipline signal.
- **Best filter state:** State A.
- **Best crop:** risk score bar + alerts table.
- **Recommended use:** both.

### 8) Data Quality
- **Screenshot name:** `data-quality.png`
- **Why it matters:** reinforces trust and analytics reliability.
- **Best filter state:** State A.
- **Best crop:** validation status chart + top checks table.
- **Recommended use:** README.

## Narrative Capture Order
1. `home-hero.png`
2. `overview-dashboard.png`
3. `strategy-performance.png`
4. `clv-analysis.png`
5. `risk-governance.png`
6. `bankroll-scenarios.png`
7. `market-performance.png`
8. `data-quality.png`

## README Embedding Snippet
```markdown
![Home](docs/screenshots/home-hero.png)
![Overview](docs/screenshots/overview-dashboard.png)
![Strategies](docs/screenshots/strategy-performance.png)
![CLV](docs/screenshots/clv-analysis.png)
![Risk](docs/screenshots/risk-governance.png)
![Bankroll](docs/screenshots/bankroll-scenarios.png)
![Markets](docs/screenshots/market-performance.png)
![Data Quality](docs/screenshots/data-quality.png)
```
