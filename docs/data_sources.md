# Data Sources

## Overview
This project uses a **hybrid demo dataset** to balance realism and reproducibility:
- Real match outcomes (teams, leagues, dates, final score)
- Simulated odds, stake sizing, and strategy picks

The goal is to keep the pipeline deterministic and offline-friendly while improving analytical credibility.

## Real Match Reference
- File: `data/samples/real_matches_reference.csv`
- Source: [football-data.co.uk](https://www.football-data.co.uk/)
- Snapshot used: 2024/2025 league-season tables
- Competitions included:
  - Premier League
  - La Liga
  - Serie A
  - Bundesliga

## Simulated Fields
These are generated locally from controlled logic in `src/ingestion/synthetic_data.py`:
- `captured_odds`
- `closing_odds`
- `stake`
- `strategy`
- `bookmaker`
- `clv`
- `payout` and `pnl` (based on market rule + final score)

## Why This Design
- Keeps the project runnable without API keys.
- Avoids fragile scraping dependencies.
- Preserves consistent test behavior.
- Adds realistic sports context for portfolio storytelling.
