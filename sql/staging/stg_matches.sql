-- Standardized match staging view
CREATE OR REPLACE VIEW stg_matches AS
SELECT
  trim(match_id) AS match_id,
  season,
  trim(league) AS league,
  initcap(trim(home_team)) AS home_team,
  initcap(trim(away_team)) AS away_team,
  CAST(kickoff_ts AS TIMESTAMP) AS kickoff_ts,
  CAST(home_goals AS INTEGER) AS home_goals,
  CAST(away_goals AS INTEGER) AS away_goals,
  CAST(home_goals AS INTEGER) + CAST(away_goals AS INTEGER) AS total_goals
FROM read_csv_auto('data/staging/matches_staging.csv');
