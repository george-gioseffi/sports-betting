"""Data models for external search results."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExternalResult:
    """One external match result from a search provider."""

    sport: str = ""
    event_date: str = ""
    home_team: str = ""
    away_team: str = ""
    event_status: str = ""  # finished | cancelled | postponed | ongoing | unknown
    home_score: int | None = None
    away_score: int | None = None
    extra_data: dict[str, Any] = field(default_factory=dict)

    @property
    def finished(self) -> bool:
        return self.event_status.lower() in ("finished", "ft", "encerrado", "finalizado")

    @property
    def cancelled(self) -> bool:
        return self.event_status.lower() in (
            "cancelled",
            "cancelado",
            "postponed",
            "adiado",
            "suspended",
            "suspenso",
        )

    @property
    def score_known(self) -> bool:
        return self.home_score is not None and self.away_score is not None


@dataclass
class MatchResult:
    """Result of trying to match a bet row to an external event."""

    found: bool = False
    confidence: float = 0.0
    external: ExternalResult | None = None
    match_reason: str = ""
