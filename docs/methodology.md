# Methodology

## 1) Synthetic Data Strategy
The MVP uses deterministic synthetic generation to guarantee reproducibility while preserving plausible relationships between:
- league and team strengths
- goal generation process
- odds levels by implied probabilities
- market outcomes and settlement logic
- strategy behavior and CLV bias

## 2) Cleaning & Standardization
Data quality starts with strict standardization:
- market canonicalization (`MONEYLINE_HOME`, `OVER_2_5`, `BTTS_YES`, `DNB_HOME`)
- team name normalization
- datetime parsing
- deduplication by entity keys

## 3) Validation Contracts
The validation layer enforces:
- domain integrity (results, markets)
- structural integrity (IDs, uniqueness)
- temporal consistency (placed <= kickoff <= settled)
- value constraints (odds > 1, stake >= 0)
- anomaly flags (extreme stakes)

## 4) KPI Computation
KPIs are computed on settled bets and segmented by analytical dimensions.  
Where needed, formulas are annualized or normalized for comparability.

## 5) Risk Governance
Risk is modeled by combining:
- realized behavior (drawdown, volatility, streaks)
- structural posture (concentration, stake intensity)
- market execution quality (CLV tendency)

The output includes both:
- a continuous risk score
- a human-readable risk profile class

## 6) Scenario Simulation
Simulation compares bankroll trajectories under distinct sizing logic:
- fixed stake
- bankroll percentage
- fractional Kelly

Risk constraints are applied to each simulation run:
- daily loss stop
- market exposure cap
- league exposure cap
- bookmaker exposure cap

## 7) Why This Is Portfolio-Grade
This project intentionally demonstrates:
- engineering quality (modular pipeline + CI)
- analytical rigor (clear formulas + risk framing)
- product thinking (dashboard + business questions)
- governance maturity (responsible-use positioning)
