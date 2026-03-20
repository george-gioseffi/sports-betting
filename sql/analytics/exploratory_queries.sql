-- Which strategy delivered best ROI-like yield?
SELECT strategy, SUM(pnl) / NULLIF(SUM(stake), 0) AS yield_pct
FROM fact_bets fb
JOIN dim_strategy ds ON fb.strategy_id = ds.strategy_id
GROUP BY strategy
ORDER BY yield_pct DESC;

-- Which markets are more volatile by daily pnl std?
WITH daily_market AS (
  SELECT
    dm.market,
    dd.date,
    SUM(fb.pnl) AS daily_pnl
  FROM fact_bets fb
  JOIN dim_market dm ON fb.market_id = dm.market_id
  JOIN dim_date dd ON fb.settled_date_id = dd.date_id
  GROUP BY dm.market, dd.date
)
SELECT
  market,
  AVG(daily_pnl) AS avg_daily_pnl,
  STDDEV_POP(daily_pnl) AS pnl_volatility
FROM daily_market
GROUP BY market
ORDER BY pnl_volatility DESC;

-- CLV trend by month
SELECT
  SUBSTR(dd.date, 1, 7) AS month,
  AVG(fb.clv) AS avg_clv
FROM fact_bets fb
JOIN dim_date dd ON fb.placed_date_id = dd.date_id
GROUP BY month
ORDER BY month;

-- Potential concentration risk by league share
SELECT
  dl.league,
  COUNT(*) AS bets,
  COUNT(*)::DOUBLE / SUM(COUNT(*)) OVER () AS bet_share
FROM fact_bets fb
JOIN dim_league dl ON fb.league_id = dl.league_id
GROUP BY dl.league
ORDER BY bet_share DESC;

-- Odds band stress behavior
SELECT
  odds_band,
  COUNT(*) AS bets,
  SUM(pnl) AS net_profit,
  SUM(pnl) / NULLIF(SUM(stake), 0) AS yield_pct
FROM fact_bets
GROUP BY odds_band
ORDER BY odds_band;
