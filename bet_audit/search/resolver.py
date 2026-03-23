"""Resolves bet outcomes from external match results and market type."""
from __future__ import annotations

import re
import unicodedata

from bet_audit.search.models import ExternalResult


def _norm(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", text)


# --------------------------------------------------------------------------- #
#  Market detection
# --------------------------------------------------------------------------- #

MARKET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("moneyline_home", re.compile(r"(moneyline|1x2|resultado).*(home|casa|mandante|time\s*1|vit.*casa)", re.I)),
    ("moneyline_away", re.compile(r"(moneyline|1x2|resultado).*(away|fora|visitante|time\s*2|vit.*fora)", re.I)),
    ("moneyline_draw", re.compile(r"(moneyline|1x2|resultado).*(draw|empate)", re.I)),
    ("over", re.compile(r"(over|acima|mais)\s*[\d.,]+", re.I)),
    ("under", re.compile(r"(under|abaixo|menos)\s*[\d.,]+", re.I)),
    ("btts_yes", re.compile(r"(btts|ambas?\s*marc|both\s*teams?\s*to\s*score).*(sim|yes)", re.I)),
    ("btts_no", re.compile(r"(btts|ambas?\s*marc|both\s*teams?\s*to\s*score).*(nao|no)", re.I)),
    ("dnb_home", re.compile(r"(dnb|draw\s*no\s*bet|empate\s*anula).*(home|casa|mandante)", re.I)),
    ("dnb_away", re.compile(r"(dnb|draw\s*no\s*bet|empate\s*anula).*(away|fora|visitante)", re.I)),
]

# Simpler fallback patterns
FALLBACK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("over", re.compile(r"\bover\b", re.I)),
    ("under", re.compile(r"\bunder\b", re.I)),
    ("btts_yes", re.compile(r"\bbtts\b", re.I)),
    ("moneyline_home", re.compile(r"\b(ml|moneyline)\b.*\bhome\b", re.I)),
    ("moneyline_away", re.compile(r"\b(ml|moneyline)\b.*\baway\b", re.I)),
]


def detect_market(description: str) -> str:
    """Detect market type from bet description. Returns 'unknown' if undetectable."""
    for market_name, pattern in MARKET_PATTERNS:
        if pattern.search(description):
            return market_name
    for market_name, pattern in FALLBACK_PATTERNS:
        if pattern.search(description):
            return market_name
    return "unknown"


def _extract_line(description: str) -> float | None:
    """Extract a numeric line value like 2.5, 1.5, etc. from description."""
    m = re.search(r"(over|under|acima|abaixo|mais|menos)\s*([\d]+[.,][\d]+)", description, re.I)
    if m:
        return float(m.group(2).replace(",", "."))
    return None


# --------------------------------------------------------------------------- #
#  Resolve outcome from external data
# --------------------------------------------------------------------------- #

def resolve_outcome(
    description: str,
    external: ExternalResult,
) -> tuple[str, str, float]:
    """Given a bet description and external result, resolve the outcome.

    Returns:
        (result, reason, confidence)
        result is one of: green, red, void, unknown
    """
    if external.cancelled:
        return "void", "evento cancelado/adiado", 0.95

    if not external.finished or not external.score_known:
        return "unknown", "evento nao finalizado ou placar desconhecido", 0.0

    hs = external.home_score  # type: ignore[assignment]
    aws = external.away_score  # type: ignore[assignment]
    total = hs + aws

    market = detect_market(description)

    if market == "moneyline_home":
        if hs > aws:
            return "green", f"mandante venceu {hs}x{aws}", 0.95
        if hs < aws:
            return "red", f"mandante perdeu {hs}x{aws}", 0.95
        return "void", f"empate {hs}x{aws} (moneyline)", 0.90

    if market == "moneyline_away":
        if aws > hs:
            return "green", f"visitante venceu {aws}x{hs}", 0.95
        if aws < hs:
            return "red", f"visitante perdeu {aws}x{hs}", 0.95
        return "void", f"empate {hs}x{aws} (moneyline)", 0.90

    if market == "moneyline_draw":
        if hs == aws:
            return "green", f"empate {hs}x{aws}", 0.95
        return "red", f"nao empatou {hs}x{aws}", 0.95

    if market == "over":
        line = _extract_line(description)
        if line is not None:
            if total > line:
                return "green", f"total {total} > {line}", 0.95
            if total < line:
                return "red", f"total {total} < {line}", 0.95
            return "void", f"total {total} = {line}", 0.90
        return "unknown", "over sem linha detectada", 0.3

    if market == "under":
        line = _extract_line(description)
        if line is not None:
            if total < line:
                return "green", f"total {total} < {line}", 0.95
            if total > line:
                return "red", f"total {total} > {line}", 0.95
            return "void", f"total {total} = {line}", 0.90
        return "unknown", "under sem linha detectada", 0.3

    if market == "btts_yes":
        if hs > 0 and aws > 0:
            return "green", f"ambas marcaram {hs}x{aws}", 0.95
        return "red", f"nao ambas marcaram {hs}x{aws}", 0.95

    if market == "btts_no":
        if hs == 0 or aws == 0:
            return "green", f"nem ambas marcaram {hs}x{aws}", 0.95
        return "red", f"ambas marcaram {hs}x{aws}", 0.95

    if market == "dnb_home":
        if hs > aws:
            return "green", f"mandante venceu {hs}x{aws} (DNB)", 0.95
        if hs < aws:
            return "red", f"mandante perdeu {hs}x{aws} (DNB)", 0.95
        return "void", f"empate {hs}x{aws} (DNB anula)", 0.95

    if market == "dnb_away":
        if aws > hs:
            return "green", f"visitante venceu {aws}x{hs} (DNB)", 0.95
        if aws < hs:
            return "red", f"visitante perdeu {aws}x{hs} (DNB)", 0.95
        return "void", f"empate {hs}x{aws} (DNB anula)", 0.95

    return "unknown", f"mercado '{market}' nao suportado para resolucao automatica", 0.0
