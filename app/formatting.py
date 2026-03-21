from __future__ import annotations

from typing import Any

import pandas as pd


def _localize_number(token: str, lang: str) -> str:
    if lang != "pt":
        return token
    return token.replace(",", "\u00a7").replace(".", ",").replace("\u00a7", ".")


def format_number(value: Any, lang: str = "en", decimals: int = 2) -> str:
    if pd.isna(value):
        return "-"
    return _localize_number(f"{float(value):,.{decimals}f}", lang)


def format_int(value: Any, lang: str = "en") -> str:
    if pd.isna(value):
        return "-"
    return _localize_number(f"{int(round(float(value))):,}", lang)


def format_pct(value: Any, lang: str = "en", decimals: int = 2) -> str:
    if pd.isna(value):
        return "-"
    pct_value = float(value) * 100
    return f"{format_number(pct_value, lang, decimals)}%"
