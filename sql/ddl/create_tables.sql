-- Core dimensional model for Sports Betting Intelligence Engine

CREATE TABLE IF NOT EXISTS dim_date (
  date_id INTEGER PRIMARY KEY,
  date DATE,
  year INTEGER,
  month INTEGER,
  day INTEGER,
  week INTEGER
);

CREATE TABLE IF NOT EXISTS dim_league (
  league_id INTEGER PRIMARY KEY,
  league VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_team (
  team_id INTEGER PRIMARY KEY,
  team_name VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_market (
  market_id INTEGER PRIMARY KEY,
  market VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_strategy (
  strategy_id INTEGER PRIMARY KEY,
  strategy VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_bookmaker (
  bookmaker_id INTEGER PRIMARY KEY,
  bookmaker VARCHAR
);

CREATE TABLE IF NOT EXISTS fact_matches (
  match_id VARCHAR PRIMARY KEY,
  season VARCHAR,
  league_id INTEGER,
  home_team_id INTEGER,
  away_team_id INTEGER,
  kickoff_ts TIMESTAMP,
  kickoff_date_id INTEGER,
  home_goals INTEGER,
  away_goals INTEGER,
  total_goals INTEGER
);

CREATE TABLE IF NOT EXISTS fact_bets (
  bet_id VARCHAR PRIMARY KEY,
  match_id VARCHAR,
  strategy_id INTEGER,
  bookmaker_id INTEGER,
  market_id INTEGER,
  league_id INTEGER,
  placed_date_id INTEGER,
  settled_date_id INTEGER,
  captured_odds DOUBLE,
  closing_odds DOUBLE,
  stake DOUBLE,
  result VARCHAR,
  payout DOUBLE,
  pnl DOUBLE,
  clv DOUBLE,
  odds_band VARCHAR
);

CREATE TABLE IF NOT EXISTS fact_results (
  bet_id VARCHAR,
  match_id VARCHAR,
  result VARCHAR,
  stake DOUBLE,
  pnl DOUBLE
);

CREATE TABLE IF NOT EXISTS fact_odds_snapshots (
  bet_id VARCHAR,
  match_id VARCHAR,
  bookmaker VARCHAR,
  market VARCHAR,
  snapshot_ts TIMESTAMP,
  captured_odds DOUBLE,
  closing_odds DOUBLE,
  clv DOUBLE
);
