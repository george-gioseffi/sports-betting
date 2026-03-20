# Metrics Specification

## Scope
Metrics are calculated on settled bets (`win`, `loss`, `push`) and are reproducible from `fact_bets`.

## Core Definitions
- **Total Bets**  
  Count of analyzed bets.

- **Win Rate**  
  `wins / settled_bets`

- **Loss Rate**  
  `losses / settled_bets`

- **Push Rate**  
  `pushes / settled_bets`

- **Net Profit**  
  `sum(pnl)`

- **Total Stake**  
  `sum(stake)`

- **ROI (capital based)**  
  `net_profit / initial_bankroll`

- **Yield (stake efficiency)**  
  `net_profit / total_stake`

- **Average Stake**  
  `mean(stake)`

- **Average Odds**  
  `mean(captured_odds)`

- **Profit Factor**  
  `sum(positive pnl) / abs(sum(negative pnl))`

- **Expectancy (per bet)**  
  `E = (P(win) * avg_win) - (P(loss) * avg_loss_abs)`  
  where `P(win)` and `P(loss)` ignore pushes.

- **Closing Line Value (CLV)**  
  `clv = (captured_odds / closing_odds) - 1`  
  Aggregated as average CLV per segment.

- **Maximum Drawdown**  
  Largest peak-to-trough percentage decline in bankroll curve.

- **Max Green Streak / Max Red Streak**  
  Longest consecutive sequence of `win` / `loss` outcomes.

- **Bankroll Volatility (annualized proxy)**  
  `std(daily_returns) * sqrt(252)`  
  where `daily_returns = daily_pnl / initial_bankroll`.

- **Sharpe-like Ratio (risk-adjusted)**  
  `mean(daily_returns) / std(daily_returns) * sqrt(252)`  
  (risk-free rate approximated as zero in MVP).

## Segment Views
The project provides KPI segmentation by:
- Strategy
- Market
- League
- Bookmaker
- Odds band
- Month

## Risk Interpretation Notes
- Positive ROI with high drawdown can still fail governance criteria.
- Positive CLV does not guarantee short-term profitability.
- Higher odds bands often increase variance and red streak probability.
- Kelly sizing can improve geometric growth but materially increases volatility if probability estimates are unstable.
