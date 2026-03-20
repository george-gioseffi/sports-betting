# Risk Governance Framework

## Responsible-Use Disclaimer
This project is intended for analytical, educational, and portfolio purposes only.  
It does not constitute financial advice, betting advice, or encouragement of gambling activity.  
The risk governance layer exists to emphasize uncertainty, volatility, and capital preservation.

## Objectives
- Control downside volatility.
- Prevent concentration risk.
- Enforce exposure discipline.
- Compare growth vs survivability trade-offs.
- Make strategy quality evaluation robust against favorable variance.

## Governance Controls

### 1) Stake Sizing Policies
- Fixed stake.
- Percentage of bankroll.
- Fractional Kelly.

### 2) Exposure Constraints
- Max exposure by market.
- Max exposure by league.
- Max exposure by bookmaker.
- Optional event-level controls (extensible in future versions).

### 3) Loss-Containment Rules
- Daily stop loss (`daily_loss_limit`).
- Drawdown threshold monitoring.

### 4) Monitoring and Alerts
- Drawdown breach alerts.
- Elevated volatility alerts.
- League concentration alerts.
- Loss-streak alerts.

## Risk Scoring Model (MVP)
Per-strategy risk score uses weighted components:
- Volatility score
- Drawdown score
- Stake intensity score
- League concentration score
- CLV penalty score
- Loss streak score

Composite score range: `0 - 100`
- `0 - 33`: Conservative
- `34 - 66`: Moderate
- `67 - 100`: Aggressive

## Governance Philosophy
- Profitability without controlled risk is not considered sustainable.
- CLV and expected value should be interpreted with uncertainty, not certainty.
- Strategy concentration can hide structural fragility.
- Capital preservation is a first-class KPI, not a secondary metric.

## Limitations
- Constraints are modeled as deterministic thresholds in MVP.
- Correlation between strategies is not yet explicitly modeled.
- No live market microstructure data in this version.

## Recommended Extensions
- Regime detection (volatility clusters).
- Cross-strategy exposure correlation matrix.
- Adaptive limits by bookmaker/league confidence.
- Stress testing with synthetic shock scenarios.
