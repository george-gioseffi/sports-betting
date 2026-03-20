# Publishing and Release Plan

## App Publishing Options

### Option A: Streamlit Community Cloud (fastest portfolio launch)
1. Push repository to GitHub.
2. Connect repository in Streamlit Community Cloud.
3. Set app entrypoint to `app/Home.py`.
4. Add secrets/env only if needed (MVP currently runs local artifacts).
5. Publish and add URL badge in README.

Best for:
- fast recruiter demos
- no infrastructure overhead

### Option B: Docker + Render/Railway/Fly.io
1. Build from `docker-compose.yml` pattern.
2. Expose Streamlit port 8501.
3. Run seed + pipeline in build/start hook.
4. Publish service URL and add observability logs.

Best for:
- infrastructure signal
- reproducible runtime

## Recommended GitHub Release Strategy

### Release `v0.1.0` - Portfolio MVP
- Initial end-to-end pipeline
- Data quality checks
- KPI and risk marts
- Streamlit multipage app
- Tests + CI

### Release `v0.2.0` - Production Readiness Layer
- Real API ingestion connectors
- richer data contracts
- improved uncertainty reporting
- deployment hardening

### Release `v0.3.0` - Advanced Analytics
- strategy correlation analysis
- dbt lineage and testing
- scenario stress testing
- confidence intervals and diagnostics

## Tagging and Changelog Convention
- Use semantic version tags: `v0.1.0`, `v0.2.0`, `v0.3.0`.
- Keep release notes concise:
  - Added
  - Improved
  - Fixed
  - Breaking (if applicable)

## README Additions After Publishing
- Add live app link badge.
- Add screenshots from `docs/screenshots/`.
- Add "Try the dashboard" section near top.
