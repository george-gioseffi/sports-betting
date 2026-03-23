"""Mock search provider for testing — returns predefined results."""
from __future__ import annotations

from bet_audit.search.base import BaseSearchProvider
from bet_audit.search.models import ExternalResult


class MockSearchProvider(BaseSearchProvider):
    """Returns a fixed set of results for any query. Useful for tests."""

    def __init__(self, results: list[ExternalResult] | None = None) -> None:
        self._results = results or [
            ExternalResult(
                sport="futebol",
                event_date="2026-01-15",
                home_team="Flamengo",
                away_team="Palmeiras",
                event_status="finished",
                home_score=2,
                away_score=1,
            ),
            ExternalResult(
                sport="futebol",
                event_date="2026-01-16",
                home_team="Barcelona",
                away_team="Real Madrid",
                event_status="finished",
                home_score=1,
                away_score=1,
            ),
            ExternalResult(
                sport="futebol",
                event_date="2026-02-01",
                home_team="Man City",
                away_team="Liverpool",
                event_status="cancelled",
                home_score=None,
                away_score=None,
            ),
        ]

    def name(self) -> str:
        return "mock"

    def search(self, query: str, event_date: str | None = None) -> list[ExternalResult]:
        import re
        import unicodedata

        def _n(t: str) -> str:
            t = t.strip().lower()
            t = unicodedata.normalize("NFKD", t)
            t = "".join(c for c in t if not unicodedata.combining(c))
            return re.sub(r"[^a-z0-9]+", "", t)

        q = _n(query)
        if not q:
            return []

        matched = []
        for r in self._results:
            if _n(r.home_team) in q or _n(r.away_team) in q or q in _n(r.home_team) or q in _n(r.away_team):
                if event_date and str(event_date)[:10] == r.event_date[:10]:
                    matched.append(r)
                elif not event_date:
                    matched.append(r)
        return matched
