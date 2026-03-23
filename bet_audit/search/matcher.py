"""Matches a bet row description to external results."""
from __future__ import annotations

import re
import unicodedata

from bet_audit.search.base import BaseSearchProvider
from bet_audit.search.models import ExternalResult, MatchResult


def _normalise(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", text)


def _team_in_query(team: str, query: str) -> bool:
    tn = _normalise(team)
    qn = _normalise(query)
    return bool(tn) and (tn in qn)


def match_bet_to_external(
    description: str,
    event_date: str | None,
    provider: BaseSearchProvider,
) -> MatchResult:
    """Try to find the best external match for a bet description."""
    if not description or not description.strip():
        return MatchResult(found=False, confidence=0.0, match_reason="descricao vazia")

    candidates = provider.search(description, event_date)
    if not candidates:
        return MatchResult(found=False, confidence=0.0, match_reason="nenhum resultado externo")

    best: ExternalResult | None = None
    best_score = 0.0

    for ext in candidates:
        score = 0.0
        home_match = _team_in_query(ext.home_team, description)
        away_match = _team_in_query(ext.away_team, description)

        if home_match and away_match:
            score += 0.7
        elif home_match or away_match:
            score += 0.4

        if event_date and ext.event_date and str(event_date)[:10] == ext.event_date[:10]:
            score += 0.3

        if score > best_score:
            best_score = score
            best = ext

    if best is None or best_score < 0.3:
        return MatchResult(found=False, confidence=best_score, match_reason="score insuficiente")

    reason_parts = []
    if _team_in_query(best.home_team, description):
        reason_parts.append(f"home={best.home_team}")
    if _team_in_query(best.away_team, description):
        reason_parts.append(f"away={best.away_team}")
    reason_parts.append(f"score={best_score:.2f}")

    return MatchResult(
        found=True,
        confidence=min(best_score, 1.0),
        external=best,
        match_reason=", ".join(reason_parts),
    )
