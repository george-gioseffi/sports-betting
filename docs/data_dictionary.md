# Data Dictionary

## Layer: Raw

### `matches_raw.csv`
- `match_id` (string): Unique match identifier.
- `season` (string): Season tag.
- `league` (string): League name.
- `home_team` (string): Home team.
- `away_team` (string): Away team.
- `kickoff_ts` (datetime): Match kickoff timestamp.
- `home_goals` (int): Home team goals.
- `away_goals` (int): Away team goals.

### `bets_raw.csv`
- `bet_id` (string): Unique bet identifier.
- `match_id` (string): Match foreign key.
- `strategy` (string): Strategy name.
- `bookmaker` (string): Bookmaker name.
- `market` (string): Market code.
- `selection` (string): Selection in market.
- `captured_odds` (float): Odds at placement.
- `closing_odds` (float): Odds near kickoff close.
- `stake` (float): Stake amount.
- `placed_ts` (datetime): Placement timestamp.
- `settled_ts` (datetime): Settlement timestamp.
- `result` (string): `win/loss/push`.
- `payout` (float): Gross payout.
- `pnl` (float): Profit and loss.
- `clv` (float): Closing line value.
- `league` (string): League denormalized for convenience.

## Layer: Staging

### `matches_staging.csv`
Raw matches with:
- standardized team names
- timestamp typing
- deduplication
- derived `total_goals`

### `bets_staging.csv`
Raw bets with:
- standardized market names
- typed numeric fields
- deduplication by `bet_id`
- league reconciliation from matches
- derived `odds_band`

## Layer: Dimensions

### `dim_date`
- `date_id` (int)
- `date` (date)
- `year` (int)
- `month` (int)
- `day` (int)
- `week` (int)

### `dim_league`
- `league_id` (int)
- `league` (string)

### `dim_team`
- `team_id` (int)
- `team_name` (string)

### `dim_market`
- `market_id` (int)
- `market` (string)

### `dim_strategy`
- `strategy_id` (int)
- `strategy` (string)

### `dim_bookmaker`
- `bookmaker_id` (int)
- `bookmaker` (string)

## Layer: Facts

### `fact_matches`
- Match-level outcomes and keys into league/team/date dimensions.

### `fact_bets`
- Bet-level measures with dimensional keys and PnL.

### `fact_odds_snapshots`
- Captured and closing odds records per bet snapshot.

### `fact_results`
- Settlement result and PnL slice.

### `fact_strategy_performance`
- Strategy-level KPI summary.

### `fact_bankroll_evolution`
- Daily bankroll time series and drawdown.

### `fact_bankroll_scenarios`
- Bet-level bankroll simulation trajectories by method.

## Layer: Marts

### `kpi_overall`
Single-row portfolio KPI snapshot.

### `mart_strategy_performance`
KPI table segmented by strategy.

### `mart_market_performance`
KPI table segmented by market.

### `mart_league_performance`
KPI table segmented by league.

### `mart_bookmaker_performance`
KPI table segmented by bookmaker.

### `mart_odds_band_performance`
KPI table segmented by odds band.

### `mart_monthly_performance`
Monthly aggregate bets, stake, pnl, yield, average clv.

### `mart_risk_scores`
Strategy risk score and profile.

### `mart_risk_alerts`
Generated risk alerts per strategy.

### `mart_bankroll_scenarios_summary`
Final bankroll and risk summary by simulation method.

### `data_quality_report`
Outcome of data quality checks.
