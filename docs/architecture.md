# Architecture

## Design Principles
- Layered data architecture (`raw -> staging -> marts`) for traceability.
- Reproducible deterministic synthetic generation (`seed` and fixed RNG).
- Business-facing marts with explicit KPI logic and risk framing.
- Reusable Python modules instead of single-script notebooks.
- SQL assets mirroring analytical entities in DuckDB.

## Data Flow
1. **Ingestion (`src/ingestion`)**
   - Generates synthetic matches and bets with plausible leagues, teams, odds, markets, and outcomes.
   - Persists raw data to `data/raw/`.
2. **Cleaning (`src/cleaning`)**
   - Standardizes market naming and team naming.
   - Parses timestamps and deduplicates records.
   - Persists standardized datasets to `data/staging/`.
3. **Validation (`src/validation`)**
   - Runs quality checks on schema integrity and domain semantics.
   - Produces `data_quality_report.csv` in marts.
4. **Analytics Engine (`src/analytics`)**
   - Builds dimensions and facts.
   - Computes KPIs and segmented performance marts.
   - Produces bankroll evolution time series.
5. **Risk Engine (`src/risk`)**
   - Calculates strategy risk scores and profile classes.
   - Emits risk alerts.
6. **Simulation Engine (`src/simulation`)**
   - Runs fixed, percentage, and fractional Kelly simulations.
   - Applies governance rules (daily loss + exposure limits).
7. **Serving**
   - Writes marts as CSV files for portability.
   - Materializes all marts and facts in DuckDB (`data/warehouse.duckdb`).
   - Streamlit app consumes marts from CSV.

## Canonical Layers
- **Raw (`data/raw`)**
  - Immutable ingestion outputs.
- **Staging (`data/staging`)**
  - Cleaned and standardized entities.
- **Marts (`data/marts`)**
  - Business-ready fact tables and analytical summaries.

## Pipeline Orchestration
Command path:
- `python -m src.main seed --matches 280 --seed 42`
- `python -m src.main pipeline`

Outputs:
- CSV marts in `data/marts`
- DuckDB warehouse in `data/warehouse.duckdb`

## Quality Gates
- Critical data quality checks can break the pipeline with:
  - `python -m src.main pipeline --fail-on-dq-error`
- CI gates:
  - Ruff lint
  - Black format check
  - Pytest suite

## Why DuckDB
- Lightweight local analytics database.
- Easy interoperability with Pandas.
- Native SQL support for showcase-grade analytics queries.
- No external service dependency for recruiter-friendly execution.
