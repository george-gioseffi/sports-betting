-- League-level performance mart
CREATE OR REPLACE VIEW mart_league_summary AS
SELECT
  league,
  COUNT(*) AS bets,
  SUM(stake) AS stake_total,
  SUM(pnl) AS net_profit,
  SUM(pnl) / NULLIF(SUM(stake), 0) AS yield_pct,
  AVG(clv) AS avg_clv,
  AVG(captured_odds) AS avg_odds,
  SUM(CASE WHEN result = 'win' THEN 1 ELSE 0 END)::DOUBLE / COUNT(*) AS win_rate
FROM stg_bets
GROUP BY league
ORDER BY net_profit DESC;
