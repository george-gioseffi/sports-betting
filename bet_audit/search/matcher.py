"""Matches a bet row description to external results."""
from __future__ import annotations

import re
import unicodedata

from bet_audit.search.base import BaseSearchProvider
from bet_audit.search.models import ExternalResult, MatchResult


# --------------------------------------------------------------------------- #
#  Team aliases — maps normalised short forms to their canonical normalised name
# --------------------------------------------------------------------------- #
TEAM_ALIASES: dict[str, list[str]] = {
    "mancity": ["manchestercity", "mcity", "mancity", "cityfc"],
    "manunited": ["manchesterunited", "manunitede", "manu", "manutd", "munited", "unitedfc"],
    "liverpool": ["liverpoolfc", "liverpoolmontevideo"],
    "barcelona": ["barcelonafc", "fcbarcelona", "barca"],
    "realmadrid": ["realmad", "realmadridcf", "rmadrid"],
    "bayern": ["bayernmunique", "bayerndemunique", "bayernmunich", "fcbayern"],
    "dortmund": ["borussiadortmund", "bvb"],
    "flamengo": ["crflamengo", "flamengofc", "flamengocr"],
    "palmeiras": ["sepalmeiras", "palmeirasfc"],
    "santos": ["santosfc"],
    "corinthians": ["sccorinithians", "corinthiansfc", "timao"],
    "vasco": ["vascodagama", "vascofc", "crvasco"],
    "fluminense": ["fluminensefc"],
    "gremio": ["gremiofc", "gremiofbpa"],
    "internacional": ["internacionalfc", "interdeportoalegre", "scinter"],
    "ajax": ["ajaxamsterdam", "ajaxfc"],
    "psv": ["psveindhoven"],
    "roma": ["asroma", "romafc"],
    "napoli": ["sscnapoli", "napolifc"],
    "celtic": ["celticfc", "celticglasgow"],
    "rangers": ["rangersfc", "glasgowrangers"],
}

# Build reverse map: alias → list of canonical names
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for canonical, aliases in TEAM_ALIASES.items():
    for alias in aliases:
        _ALIAS_TO_CANONICAL[alias] = canonical
    _ALIAS_TO_CANONICAL[canonical] = canonical


def _normalise(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", text)


def _expand_team_names(team: str) -> list[str]:
    """Return all normalised forms of a team name (canonical + aliases)."""
    tn = _normalise(team)
    if not tn:
        return []

    forms = {tn}

    # Check if this team has a canonical entry
    if tn in _ALIAS_TO_CANONICAL:
        canon = _ALIAS_TO_CANONICAL[tn]
        forms.add(canon)
        # Add all aliases of the canonical
        if canon in TEAM_ALIASES:
            forms.update(TEAM_ALIASES[canon])
    else:
        # Check if tn is a known canonical
        if tn in TEAM_ALIASES:
            forms.update(TEAM_ALIASES[tn])

    return list(forms)


def _team_in_query(team: str, query: str) -> bool:
    """Check if any form of the team name appears in the query."""
    qn = _normalise(query)
    if not qn:
        return False

    for form in _expand_team_names(team):
        if form and len(form) >= 3 and form in qn:
            return True

    return False


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

        # Flexible date matching: exact date or within +/- 60 days
        if event_date and ext.event_date:
            bet_date = str(event_date)[:10]
            ext_date = ext.event_date[:10]
            if bet_date == ext_date:
                score += 0.3
            else:
                try:
                    from datetime import datetime
                    bd = datetime.strptime(bet_date, "%Y-%m-%d")
                    ed = datetime.strptime(ext_date, "%Y-%m-%d")
                    diff = abs((bd - ed).days)
                    if diff <= 60:
                        score += 0.15
                except (ValueError, TypeError):
                    pass

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
