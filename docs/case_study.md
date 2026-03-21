# Case Study: Sports Betting Intelligence Engine

## Context

Sports strategy evaluation usually stops at "is it profitable?" — but profit alone is noisy. A strategy can show positive returns for months and still be fragile: concentrated in one league, riding variance, or ignoring drawdown behavior. The real question is whether the edge is durable, governable, and risk-aware.

This project builds an analytics platform that answers that question.

## Problem

Organizations analyzing sports markets typically work with fragmented data: spreadsheets, ad hoc scripts, one-off dashboards. That creates blind spots:

- No consistent methodology across strategies
- No separation between edge and variance
- No risk governance or exposure monitoring
- No way to compare how different sizing rules affect survivability

## What makes this project different

This is not a prediction model or a "pick of the day" tool. It is a **data product** focused on evaluating the quality of past decisions — combining performance metrics, risk scoring, and scenario simulation in one pipeline.

The dataset is hybrid by design: real football match results (Premier League, La Liga, Serie A, Bundesliga) grounded with simulated odds, stakes, and picks. This keeps the project reproducible and offline while preserving realistic match context.

Five strategies with different profiles generate meaningful analytical tension:

- **sharp_value**: selective, high CLV, positive yield — the disciplined model
- **league_expert**: decent CLV but breakeven results — close but not enough edge
- **momentum**: moderate CLV, negative yield — can't convert signal into profit
- **btts_hunter**: market specialist with high drawdown — fragile despite conviction
- **high_volume**: negative CLV, high exposure, worst risk profile — overtrading without edge

This spread is deliberate. It creates the kind of trade-offs that real analysts face: a strategy can look profitable and still fail governance, or show strong CLV but bleed capital through sizing mistakes.

## Architecture

The pipeline follows a layered data model:

- **raw**: immutable ingestion from match and bet sources
- **staging**: cleaned and standardized entities
- **marts**: fact tables, dimensions, KPI summaries, risk scores, simulation results
- **warehouse**: DuckDB materialization for SQL exploration
- **app**: multipage Streamlit dashboard with global filters and bilingual support

## Analytical layer

Core KPIs include ROI, yield, CLV, profit factor, expectancy, drawdown, Sharpe-like ratio, streaks, and bankroll volatility — computed per strategy, market, league, bookmaker, odds band, and period.

The CLV analysis page is particularly useful for separating execution quality from outcome luck. sharp_value sits in the upper-right quadrant (high CLV, positive yield), while high_volume clusters in the lower-left (negative CLV, negative yield). That visual tells a clear story about pricing discipline.

## Risk governance

Each strategy receives a composite risk score (0-100) based on six weighted components: volatility, drawdown, stake intensity, league concentration, CLV penalty, and loss streak length. Strategies are classified as Conservative, Moderate, or Aggressive.

The alert system flags specific breaches — drawdown limits, elevated volatility, concentration thresholds — giving a governance layer that goes beyond raw PnL.

In the current dataset, high_volume is the only Aggressive-profile strategy, and sharp_value is the only Conservative one. That contrast makes the risk panel useful rather than decorative.

## App experience

The Streamlit app has 8 pages: Home, Overview, Strategies, Markets, CLV, Bankroll, Risk, and Data Quality. All pages share global filters (strategy, league, market, method, date range) applied through the sidebar.

The app supports English and Portuguese with a sidebar toggle. Labels, KPI cards, chart titles, table headers, and numeric formatting (decimal separators, thousands grouping) adapt to the selected language.

Charts use Plotly with a clean light theme. Tables are formatted with locale-aware numbers. The visual hierarchy follows a consistent pattern: header, note, KPI strip, charts, detail tables.

## What changed in the latest iteration

The project went through a focused round of improvements aimed at credibility and presentation quality:

- **Data narrative**: strategies were recalibrated so the dashboard tells a real story — one winner, one breakeven, three losers with different failure modes. Previously all strategies were deeply negative, which undermined the analytical value.
- **Strategy diversity**: expanded from 3 to 5 strategies with distinct profiles, making charts and comparisons more substantive.
- **Test coverage**: expanded from 12 to 42 tests covering actual logic — drawdown calculations, Kelly fraction boundaries, market resolution, daily loss limits — not just output shapes.
- **Code structure**: the 630-line `common.py` was split into `translations.py`, `formatting.py`, `filters.py`, and `components.py` with backward-compatible re-exports.
- **Documentation**: removed marketing-oriented docs that added bulk without substance. The README was rewritten to be direct and practical.
- **Strategy names**: changed from generic labels to natural names that reflect what each model actually does.

## Key takeaways

1. sharp_value is the only strategy that sustains positive yield (+6.9%), and it also has the lowest risk score and smallest drawdown. Edge + discipline = results.
2. league_expert has decent CLV (+5%) but breaks even — suggesting the signal exists but sizing or market selection dilutes it.
3. high_volume generates the most bets but has negative CLV and the worst risk profile. Volume without edge destroys capital.
4. Bankroll simulation shows that Kelly sizing skips more bets due to exposure limits but preserves capital better than fixed staking.
5. The risk governance layer is not decorative — it identifies high_volume as Aggressive before you even look at its PnL.

## Limitations

- Offline dataset, not a live production feed.
- No cross-strategy covariance modeling.
- No intraday odds ladder or market microstructure data.
- Risk score is a governance aid, not a formal ruin-probability model.
- Synthetic pricing means CLV distributions are controlled, not observed from real markets.

## Next steps

- Integrate real odds/match APIs for live data ingestion.
- Add uncertainty intervals and bootstrap confidence bands.
- Add correlation-aware portfolio exposure constraints.
