-- Strategy-level KPI mart
CREATE OR REPLACE VIEW mart_strategy_summary AS
WITH base AS (
  SELECT
    strategy,
    COUNT(*) AS total_bets,
    SUM(stake) AS total_stake,
    SUM(pnl) AS net_profit,
    AVG(captured_odds) AS avg_odds,
    AVG(clv) AS avg_clv,
    SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN result = 'loss' THEN 1 ELSE 0 END) AS losses,
    SUM(CASE WHEN result = 'push' THEN 1 ELSE 0 END) AS pushes
  FROM stg_bets
  GROUP BY strategy
)
SELECT
  strategy,
  total_bets,
  total_stake,
  net_profit,
  net_profit / NULLIF(total_stake, 0) AS yield_pct,
  avg_odds,
  avg_clv,
  wins::DOUBLE / NULLIF(total_bets, 0) AS win_rate,
  losses::DOUBLE / NULLIF(total_bets, 0) AS loss_rate,
  pushes::DOUBLE / NULLIF(total_bets, 0) AS push_rate,
  SUM(CASE WHEN net_profit > 0 THEN net_profit ELSE 0 END)
    OVER () / NULLIF(ABS(SUM(CASE WHEN net_profit < 0 THEN net_profit ELSE 0 END) OVER ()), 0)
    AS portfolio_profit_factor
FROM base
ORDER BY net_profit DESC;
