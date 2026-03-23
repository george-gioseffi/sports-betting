"""Detection of 'desplanilhadas' — bets with spreadsheet data integrity issues."""
from __future__ import annotations

import pandas as pd


def detect_desplanilhadas(df: pd.DataFrame) -> pd.Series:
    """Return a boolean Series marking rows that look like spreadsheet errors.

    A row is flagged as 'desplanilhada' when the data looks incomplete,
    contradictory, or suggests a recording failure in the original spreadsheet.
    """
    flags = pd.Series(False, index=df.index)

    # 1. Status empty AND lucro empty/nan
    status_empty = df["status_original"].fillna("").astype(str).str.strip().eq("")
    lucro_missing = df["lucro"].isna()
    flags |= status_empty & lucro_missing

    # 2. Status empty, lucro is exactly zero, and there's a non-trivial description
    #    (looks like the bet happened but was never settled / recorded)
    has_desc = df["descricao"].fillna("").astype(str).str.len().gt(5)
    lucro_zero = df["lucro"].fillna(1).eq(0)
    flags |= status_empty & lucro_zero & has_desc

    # 3. Strong contradiction: status says green but lucro is clearly negative
    #    (not a minor rounding issue but a real sign mismatch)
    resultado_texto = df.get("resultado_texto", pd.Series("", index=df.index))
    flags |= (resultado_texto == "green") & (df["lucro"] < -1)

    # 4. Strong contradiction: status says red but lucro is clearly positive
    flags |= (resultado_texto == "red") & (df["lucro"] > 1)

    # 5. External result found but spreadsheet has no coherent classification
    #    (external says finished but row has empty status and zero lucro)
    if "resultado_externo" in df.columns:
        ext_found = df["resultado_externo"].fillna("").astype(str).ne("")
        ext_found &= df["resultado_externo"] != "unknown"
        flags |= ext_found & status_empty & lucro_zero

    # 6. Has odd and stake but no result at all
    has_odd = df.get("odd", pd.Series(float("nan"), index=df.index)).notna()
    has_stake = df.get("stake", pd.Series(float("nan"), index=df.index)).notna()
    resultado_norm = df.get("resultado_norm", pd.Series("unknown", index=df.index))
    flags |= has_odd & has_stake & has_desc & status_empty & (resultado_norm == "unknown")

    return flags


def classify_desplanilhada_reason(row: pd.Series) -> str:
    """Return a human-readable reason for why a row is desplanilhada."""
    reasons = []
    status = str(row.get("status_original", "")).strip()
    lucro = row.get("lucro")
    desc = str(row.get("descricao", "")).strip()
    resultado_texto = str(row.get("resultado_texto", ""))

    if not status and (pd.isna(lucro) or lucro is None):
        reasons.append("status e lucro ausentes")
    if not status and lucro == 0 and len(desc) > 5:
        reasons.append("status vazio com lucro zero e descricao presente")
    if resultado_texto == "green" and isinstance(lucro, (int, float)) and lucro < -1:
        reasons.append(f"status indica green mas lucro={lucro}")
    if resultado_texto == "red" and isinstance(lucro, (int, float)) and lucro > 1:
        reasons.append(f"status indica red mas lucro={lucro}")
    if not status and str(row.get("resultado_externo", "")) not in ("", "unknown"):
        reasons.append("resultado externo encontrado mas planilha sem classificacao")

    return "; ".join(reasons) if reasons else "dados incompletos ou contraditorios"
