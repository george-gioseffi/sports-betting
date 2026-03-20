# Case Study: Sports Betting Intelligence Engine

## Context
Teams analyzing sports-market strategies often work with fragmented data across spreadsheets, ad hoc scripts, and disconnected reports. That makes it hard to separate real edge from short-term variance.

## Problem
The organization needs a system that can:
- consolidate picks, odds, and outcomes into a reliable analytical model
- measure performance with consistent formulas
- quantify risk posture and concentration
- simulate bankroll outcomes under different stake rules
- support clear, repeatable, and governance-aware decisions

## Approach
I built an end-to-end analytics platform with a layered architecture:
1. Ingestion (synthetic plus future API-ready hooks)
2. Cleaning and standardization
3. Data quality contracts
4. Analytics marts and KPI engine
5. Risk governance and alerts
6. Scenario simulation for bankroll management
7. Streamlit interface for executive and exploratory views

## Architecture
- `raw`: immutable event and odds captures
- `staging`: standardized entities and typed fields
- `marts`: decision-ready facts, dimensions, and KPI summaries
- `warehouse`: DuckDB materialization for SQL exploration
- `app`: multipage Streamlit interface with global filters

## Methodology
- Generate deterministic synthetic data with plausible market behavior.
- Normalize markets and entities for semantic consistency.
- Enforce quality constraints (domain, temporal, structural).
- Compute KPIs (ROI, yield, CLV, expectancy, drawdown, volatility).
- Score strategies with a governance-oriented risk model.
- Compare bankroll trajectories under fixed, percentage, and Kelly sizing.

## Key Insights (Example Outputs)
- Strategies with positive net profit can still exhibit unacceptable drawdown.
- Positive CLV and positive PnL do not always move together in short windows.
- High-odds segments can increase variance disproportionately.
- Exposure concentration in a single league can raise systemic risk.
- Simulation highlights that sizing method selection materially impacts survivability.

## Limitations
- MVP synthetic baseline, not a live production feed.
- No explicit cross-strategy covariance modeling in current version.
- No intraday odds ladder or microstructure data.
- Risk score is a governance aid, not a guaranteed ruin-probability model.

## Next Steps
- Integrate real odds/match APIs.
- Add dbt for lineage, tests, and model contracts.
- Add confidence intervals and uncertainty-aware reporting.
- Add correlation-aware portfolio constraints.
- Deploy Streamlit app to public cloud with release tagging.
