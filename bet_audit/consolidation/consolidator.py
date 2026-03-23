"""Final verdict consolidator — applies priority chain to produce VEREDITO_FINAL."""
from __future__ import annotations

import pandas as pd

from bet_audit.consolidation.desplanilhadas import classify_desplanilhada_reason, detect_desplanilhadas

# Map normalised results to verdict labels
_KEEP_MAP = {"green": "MANTER_GREEN", "red": "MANTER_RED", "void": "MANTER_ANULADA"}
_CORRECT_MAP = {"green": "CORRIGIR_PARA_GREEN", "red": "CORRIGIR_PARA_RED", "void": "CORRIGIR_PARA_ANULADA"}


def consolidate(df: pd.DataFrame) -> pd.DataFrame:
    """Add final verdict columns to the dataframe.

    Priority chain:
      1. External result (high confidence)
      2. Deterministic rule
      3. AI classification
      4. Manual review fallback

    Adds columns:
      - veredito_final
      - fonte_veredito_final
      - motivo_veredito_final
      - confidence_final
      - prioridade_revisao (1=urgent, 2=medium, 3=low, 0=none)
      - is_desplanilhada
      - motivo_desplanilhada
    """
    out = df.copy()

    # Ensure needed columns exist with defaults
    for col, default in [
        ("resultado_externo", ""),
        ("confianca_externo", 0.0),
        ("motivo_externo", ""),
        ("classificacao_ia", ""),
        ("confianca_ia", 0.0),
        ("resultado_norm", "unknown"),
        ("resultado_texto", "unknown"),
    ]:
        if col not in out.columns:
            out[col] = default

    out["resultado_externo"] = out["resultado_externo"].fillna("").astype(str)
    out["classificacao_ia"] = out["classificacao_ia"].fillna("").astype(str)
    out["confianca_externo"] = pd.to_numeric(out["confianca_externo"], errors="coerce").fillna(0.0)
    out["confianca_ia"] = pd.to_numeric(out["confianca_ia"], errors="coerce").fillna(0.0)

    # Detect desplanilhadas
    out["is_desplanilhada"] = detect_desplanilhadas(out)
    out["motivo_desplanilhada"] = ""
    desplan_mask = out["is_desplanilhada"]
    if desplan_mask.any():
        out.loc[desplan_mask, "motivo_desplanilhada"] = out.loc[desplan_mask].apply(
            classify_desplanilhada_reason, axis=1
        )

    # Initialise verdict columns
    n = len(out)
    veredito = pd.Series("REVISAO_MANUAL", index=out.index)
    fonte = pd.Series("", index=out.index)
    motivo = pd.Series("", index=out.index)
    confidence = pd.Series(0.0, index=out.index)
    prioridade = pd.Series(2, index=out.index)  # default medium

    # ------ LAYER 4: fallback manual ------
    # Already initialised above.

    # ------ LAYER 3: AI classification ------
    ai_valid = out["classificacao_ia"].isin(["green", "red", "void"]) & (out["confianca_ia"] >= 0.5)
    for idx in out.index[ai_valid]:
        ai_cls = out.at[idx, "classificacao_ia"]
        rule_cls = out.at[idx, "resultado_norm"]
        if ai_cls == rule_cls:
            veredito.at[idx] = _KEEP_MAP.get(ai_cls, "REVISAO_MANUAL")
        else:
            veredito.at[idx] = _CORRECT_MAP.get(ai_cls, "REVISAO_MANUAL")
        fonte.at[idx] = "ia"
        motivo.at[idx] = f"IA classificou como {ai_cls} (conf={out.at[idx, 'confianca_ia']:.2f})"
        confidence.at[idx] = out.at[idx, "confianca_ia"]
        prioridade.at[idx] = 3

    # ------ LAYER 2: deterministic rule ------
    rule_known = out["resultado_norm"].isin(["green", "red", "void"])
    for idx in out.index[rule_known]:
        rule_cls = out.at[idx, "resultado_norm"]
        veredito.at[idx] = _KEEP_MAP.get(rule_cls, "REVISAO_MANUAL")
        fonte.at[idx] = "regra"
        motivo.at[idx] = f"regra deterministica: {rule_cls}"
        confidence.at[idx] = 0.85
        prioridade.at[idx] = 0

    # ------ LAYER 1: external result (highest priority) ------
    ext_valid = out["resultado_externo"].isin(["green", "red", "void"]) & (out["confianca_externo"] >= 0.5)
    for idx in out.index[ext_valid]:
        ext_cls = out.at[idx, "resultado_externo"]
        rule_cls = out.at[idx, "resultado_norm"]
        if ext_cls == rule_cls:
            veredito.at[idx] = _KEEP_MAP.get(ext_cls, "REVISAO_MANUAL")
            motivo.at[idx] = f"resultado externo confirma: {ext_cls} ({out.at[idx, 'motivo_externo']})"
        else:
            veredito.at[idx] = _CORRECT_MAP.get(ext_cls, "REVISAO_MANUAL")
            motivo.at[idx] = (
                f"resultado externo corrige {rule_cls}->{ext_cls} ({out.at[idx, 'motivo_externo']})"
            )
        fonte.at[idx] = "externo"
        confidence.at[idx] = out.at[idx, "confianca_externo"]
        prioridade.at[idx] = 0

    # ------ Override: desplanilhadas ------
    for idx in out.index[out["is_desplanilhada"]]:
        if fonte.at[idx] not in ("externo",):
            veredito.at[idx] = "DESPLANILHADA"
            if not fonte.at[idx]:
                fonte.at[idx] = "desplanilhada"
            motivo.at[idx] = out.at[idx, "motivo_desplanilhada"]
            prioridade.at[idx] = 1

    out["veredito_final"] = veredito
    out["fonte_veredito_final"] = fonte
    out["motivo_veredito_final"] = motivo
    out["confidence_final"] = confidence
    out["prioridade_revisao"] = prioridade

    return out
