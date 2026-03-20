# Assumptions and Limitations

## Assumptions
- Odds use decimal format.
- Bets are treated as pre-match in this MVP.
- Settlement timing is simplified and deterministic.
- Strategy behavior is represented by probabilistic templates.
- CLV is estimated by captured-vs-closing odds ratio.
- Risk-free rate is approximated as zero in Sharpe-like calculations.

## Limitations
- No live API connector in the MVP baseline.
- No intraday odds ladder/history (single captured and closing snapshot).
- No explicit covariance model between strategies.
- No transaction costs or liquidity slippage model.
- No bookmaker account constraints (limits, delays, rejection probabilities).

## Interpretation Cautions
- Positive short-window ROI can be variance-driven.
- CLV is a useful signal but not a guarantee of future returns.
- Synthetic data is for system demonstration, not market inference.
- Risk score is a governance aid, not a perfect model of ruin probability.

## Extension Priorities
- Integrate real event and odds feeds.
- Add confidence intervals and bootstrap uncertainty bands.
- Add Bayesian shrinkage for low-sample strategy estimates.
- Add cross-strategy correlation-aware exposure constraints.
