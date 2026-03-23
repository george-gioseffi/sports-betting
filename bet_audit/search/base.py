"""Abstract base for search providers."""
from __future__ import annotations

from abc import ABC, abstractmethod

from bet_audit.search.models import ExternalResult


class BaseSearchProvider(ABC):
    """Contract every search provider must fulfill."""

    @abstractmethod
    def search(self, query: str, event_date: str | None = None) -> list[ExternalResult]:
        """Return candidate external results for a free-text query."""

    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
