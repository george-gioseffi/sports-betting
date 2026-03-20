-- Standardized betting staging view
CREATE OR REPLACE VIEW stg_bets AS
SELECT
  trim(bet_id) AS bet_id,
  trim(match_id) AS match_id,
  trim(strategy) AS strategy,
  trim(bookmaker) AS bookmaker,
  upper(trim(market)) AS market,
  trim(selection) AS selection,
  CAST(captured_odds AS DOUBLE) AS captured_odds,
  CAST(closing_odds AS DOUBLE) AS closing_odds,
  CAST(stake AS DOUBLE) AS stake,
  CAST(placed_ts AS TIMESTAMP) AS placed_ts,
  CAST(settled_ts AS TIMESTAMP) AS settled_ts,
  lower(trim(result)) AS result,
  CAST(payout AS DOUBLE) AS payout,
  CAST(pnl AS DOUBLE) AS pnl,
  CAST(clv AS DOUBLE) AS clv,
  trim(league) AS league,
  trim(odds_band) AS odds_band
FROM read_csv_auto('data/staging/bets_staging.csv');
