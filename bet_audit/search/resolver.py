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
#  Market detection — expanded with Portuguese betting patterns
# --------------------------------------------------------------------------- #

MARKET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # --- Over / Under (PT + EN) ---
    # "Over 2.5", "Mais de 2.5", "Acima de 1.5", "+2.5 gols", "o2.5", "O1.5"
    ("over", re.compile(
        r"(?:"
        r"over\s*[\d.,]+"
        r"|(?:mais|acima)\s+(?:de\s+)?[\d.,]+"
        r"|\bo[\d]+[.,][\d]+"
        r"|\+[\d]+[.,][\d]+\s*(?:gol|gols|goals)"
        r")", re.I)),
    # "Under 2.5", "Menos de 2.5", "Abaixo de 1.5", "U2.5"
    ("under", re.compile(
        r"(?:"
        r"under\s*[\d.,]+"
        r"|(?:menos|abaixo)\s+(?:de\s+)?[\d.,]+"
        r"|\bu[\d]+[.,][\d]+"
        r"|\-[\d]+[.,][\d]+\s*(?:gol|gols|goals)"
        r")", re.I)),

    # --- BTTS (both orders: "Sim / Ambas marcam" and "Ambas marcam / Sim") ---
    ("btts_yes", re.compile(
        r"(?:"
        r"(?:btts|ambas?\s*(?:os\s*times?\s*)?marc|both\s*teams?\s*(?:to\s*)?score|ambas\s*equipes?\s*marc).*(?:sim|yes)"
        r"|(?:sim|yes).*(?:btts|ambas?\s*(?:os\s*times?\s*)?marc|both\s*teams?\s*(?:to\s*)?score|ambas\s*equipes?\s*marc)"
        r"|(?:ambas?\s*marc|ambas\s*equipes?\s*marc|ambos?\s*(?:os\s*times?\s*)?marc|both\s*teams?\s*(?:to\s*)?score)"
        r"|\be\s+ambas\s*marc"
        r"|\bambas$"
        r")", re.I)),
    ("btts_no", re.compile(
        r"(?:"
        r"(?:btts|ambas?\s*(?:os\s*times?\s*)?marc|both\s*teams?\s*(?:to\s*)?score).*(?:nao|no\b)"
        r"|(?:nao|no\b).*(?:btts|ambas?\s*(?:os\s*times?\s*)?marc|both\s*teams?\s*(?:to\s*)?score)"
        r"|n[aã]o\s+ambas?\s*(?:os\s*times?\s*)?marc"
        r"|ambas?\s*n[aã]o\s*marc"
        r")", re.I)),

    # --- 1X2 / Moneyline ---
    ("moneyline_home", re.compile(
        r"(?:moneyline|1x2|resultado\s*final?)\s*.*(?:home|casa|mandante|time\s*1|vit.*casa)", re.I)),
    ("moneyline_away", re.compile(
        r"(?:moneyline|1x2|resultado\s*final?)\s*.*(?:away|fora|visitante|time\s*2|vit.*fora)", re.I)),
    ("moneyline_draw", re.compile(
        r"(?:moneyline|1x2|resultado\s*final?)\s*.*(?:draw|empate)", re.I)),

    # --- DNB ---
    ("dnb_home", re.compile(r"(?:dnb|draw\s*no\s*bet|empate\s*anula).*(?:home|casa|mandante)", re.I)),
    ("dnb_away", re.compile(r"(?:dnb|draw\s*no\s*bet|empate\s*anula).*(?:away|fora|visitante)", re.I)),

    # --- Handicap ---
    ("handicap", re.compile(
        r"(?:"
        r"handicap"
        r"|[\-+][\d]+[.,][\d]+\s*(?:ah|handicap)"
        r"|\bah\s+[\-+]?[\d]"
        r"|\b\-[\d]+[.,][\d]+\s*ah\b"
        r"|\bha\s+[\-+]"
        r")", re.I)),

    # --- Double Chance ---
    ("double_chance", re.compile(
        r"(?:"
        r"chance\s*dupla"
        r"|double\s*chance"
        r"|\bdc\b"
        r"|\bou\s+empate\b"
        r")", re.I)),

    # --- HT/FT ---
    ("ht_ft", re.compile(
        r"(?:"
        r"ht\s*/\s*ft"
        r"|ht/ft"
        r"|intervalo\s*/\s*final"
        r"|resultado\s+intervalo"
        r"|1[ºo]\s*tempo.*(?:1x2|resultado)"
        r"|(?:1x2|resultado).*1[ºo]\s*tempo"
        r")", re.I)),

    # --- Corners / Escanteios ---
    ("corners", re.compile(
        r"(?:"
        r"escanteios?"
        r"|cantos?"
        r"|corners?"
        r"|\besc\b"
        r")", re.I)),

    # --- Cards / Cartoes ---
    ("cards", re.compile(
        r"(?:"
        r"cart[oõ]es?"
        r"|cart[aã]o"
        r"|cards?"
        r")", re.I)),

    # --- Player Props ---
    ("player_props", re.compile(
        r"(?:"
        r"duplo\s*duplo"
        r"|triple\s*double"
        r"|player\s*props?"
        r"|\b\d+\+?\s*pts\b"
        r"|\b\d+\+?\s*rebounds?\b"
        r"|\b\d+\+?\s*assists?\b"
        r"|marcar?\s+(?:a\s+)?qualquer\s+momento"
        r"|anytime\b"
        r"|gol\s*a\s*qualquer"
        r"|jogador\s*(?:para\s*)?marc"
        r")", re.I)),

    # --- Shots ---
    ("shots", re.compile(
        r"(?:"
        r"chutes?\s*(?:no\s*gol|a\s*gol)?"
        r"|shots?\s*(?:on\s*(?:target|goal))?"
        r"|\bsot\b"
        r"|\bsots?\b"
        r")", re.I)),
]

# Simpler fallback patterns — catch common shorthand
FALLBACK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("over", re.compile(r"\bover\b", re.I)),
    ("under", re.compile(r"\bunder\b", re.I)),
    ("btts_yes", re.compile(r"\bbtts\b", re.I)),
    # "ML" standalone or "X ML" or "ML X"
    ("moneyline", re.compile(r"\bml\b", re.I)),
    # "vence" / "vencem" / "vencer" / "ganha" / "ganhar" (generic moneyline indicator)
    ("moneyline", re.compile(
        r"(?:"
        r"\bvence[mr]?\b"
        r"|\bganh[ao]r?\b"
        r"|\bpara\s+ganhar\b"
        r"|\bpara\s+vencer\b"
        r"|\bvit[oó]ria\b"
        r"|\bwin\b"
        r"|\bto\s+win\b"
        r")", re.I)),
    # "Resultado Final" without further qualifier
    ("moneyline", re.compile(r"\bresultado\s*final\b", re.I)),
    # "-1.5 AH" / "Liverpool -1.5" / "+ 1,5"
    ("handicap", re.compile(r"[\-+]\s*\d+[.,]\d+", re.I)),
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
    # Try explicit "over/under/mais/menos de X.X" patterns
    m = re.search(
        r"(?:over|under|acima|abaixo|mais|menos)\s*(?:de\s*)?([\d]+[.,][\d]+)",
        description, re.I,
    )
    if m:
        return float(m.group(1).replace(",", "."))

    # Try shorthand "o2.5" / "u2.5" / "O1.5"
    m = re.search(r"\b[oOuU]([\d]+[.,][\d]+)", description)
    if m:
        return float(m.group(1).replace(",", "."))

    # Try "+X.X gols" / "X.X gols"
    m = re.search(r"[+]?([\d]+[.,][\d]+)\s*(?:gol|gols|goals)", description, re.I)
    if m:
        return float(m.group(1).replace(",", "."))

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

    if market in ("moneyline_home", "moneyline"):
        # For generic "moneyline", we can try to resolve if the description
        # references a specific team — but for now treat as home moneyline
        # only when the market was explicitly "moneyline_home"
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

    if market == "double_chance":
        # Can't resolve without knowing which DC option was bet on
        return "unknown", f"mercado double_chance detectado mas opcao nao resolvida", 0.3

    # For markets we detect but can't resolve automatically, return with the
    # market name so downstream knows what was found
    return "unknown", f"mercado '{market}' nao suportado para resolucao automatica", 0.0
