"""CSV-based search provider — reads a local CSV of known results."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

from bet_audit.search.base import BaseSearchProvider
from bet_audit.search.models import ExternalResult


def _normalise(text: str) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", text)


class CSVSearchProvider(BaseSearchProvider):
    """Searches a local CSV file for external event results.

    Expected CSV columns (flexible naming via synonyms):
        sport, event_date, home_team, away_team, event_status,
        home_score, away_score, extra_data_json
    """

    COLUMN_MAP = {
        "sport": ["sport", "esporte", "modalidade"],
        "event_date": ["event_date", "data", "date", "data_evento"],
        "home_team": ["home_team", "home", "mandante", "time_casa"],
        "away_team": ["away_team", "away", "visitante", "time_fora"],
        "event_status": ["event_status", "status", "estado", "resultado_evento"],
        "home_score": ["home_score", "gols_casa", "score_home", "placar_casa"],
        "away_score": ["away_score", "gols_fora", "score_away", "placar_fora"],
        "extra_data_json": ["extra_data_json", "extra", "extras"],
    }

    def __init__(self, csv_path: str | Path) -> None:
        self._path = Path(csv_path)
        self._df = self._load()

    def _resolve_col(self, df_cols: list[str], synonyms: list[str]) -> str | None:
        normed = {_normalise(c): c for c in df_cols}
        for syn in synonyms:
            if _normalise(syn) in normed:
                return normed[_normalise(syn)]
        return None

    def _load(self) -> pd.DataFrame:
        if not self._path.exists():
            raise FileNotFoundError(f"CSV de resultados nao encontrado: {self._path}")
        raw = pd.read_csv(self._path, dtype=str)
        raw.columns = [c.strip() for c in raw.columns]
        mapped: dict[str, pd.Series] = {}
        for logical, synonyms in self.COLUMN_MAP.items():
            col = self._resolve_col(list(raw.columns), synonyms)
            if col is not None:
                mapped[logical] = raw[col]
            else:
                mapped[logical] = pd.Series("", index=raw.index)
        df = pd.DataFrame(mapped)
        df["_home_norm"] = df["home_team"].apply(_normalise)
        df["_away_norm"] = df["away_team"].apply(_normalise)
        return df

    def name(self) -> str:
        return f"csv:{self._path.name}"

    def search(self, query: str, event_date: str | None = None) -> list[ExternalResult]:
        q = _normalise(query)
        if not q:
            return []

        candidates = self._df[
            self._df["_home_norm"].apply(lambda h: h in q or q in h if h else False)
            | self._df["_away_norm"].apply(lambda a: a in q or q in a if a else False)
        ]

        if event_date and not candidates.empty:
            date_str = str(event_date)[:10]
            date_match = candidates[candidates["event_date"].str[:10] == date_str]
            if not date_match.empty:
                candidates = date_match

        results: list[ExternalResult] = []
        for _, row in candidates.iterrows():
            hs_raw = str(row.get("home_score", "")).strip()
            aws_raw = str(row.get("away_score", "")).strip()
            hs = int(float(hs_raw)) if hs_raw not in ("", "nan", "None", "none") else None
            aws = int(float(aws_raw)) if aws_raw not in ("", "nan", "None", "none") else None
            results.append(
                ExternalResult(
                    sport=str(row.get("sport", "")),
                    event_date=str(row.get("event_date", "")),
                    home_team=str(row.get("home_team", "")),
                    away_team=str(row.get("away_team", "")),
                    event_status=str(row.get("event_status", "")),
                    home_score=hs,
                    away_score=aws,
                )
            )
        return results
