"""Export audit results to Excel with multiple tabs and CSVs."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd


def _filter_tab(df: pd.DataFrame, column: str, values: list[str]) -> pd.DataFrame:
    if column not in df.columns:
        return pd.DataFrame()
    return df[df[column].isin(values)].copy()


def export_audit(
    df: pd.DataFrame,
    output_dir: Path,
    metadata: dict,
) -> dict[str, str]:
    """Export the fully audited dataframe to Excel + CSVs.

    Creates tabs:
        resumo, suspeitas, desplanilhadas, revisao_manual,
        corrigir_green_red, sem_match_externo, auditadas_com_ia, base_completa
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = output_dir / f"auditoria_{ts}.xlsx"
    json_path = output_dir / f"resumo_auditoria_{ts}.json"

    # Build summary
    total = len(df)
    vereditos = df["veredito_final"].value_counts().to_dict() if "veredito_final" in df.columns else {}
    fontes = df["fonte_veredito_final"].value_counts().to_dict() if "fonte_veredito_final" in df.columns else {}

    resumo_rows = [
        ("total_linhas_auditadas", total),
        ("periodo_inicio", str(df["data_hora"].min()) if "data_hora" in df.columns else ""),
        ("periodo_fim", str(df["data_hora"].max()) if "data_hora" in df.columns else ""),
    ]
    for k, v in sorted(vereditos.items()):
        resumo_rows.append((f"veredito_{k}", v))
    for k, v in sorted(fontes.items()):
        resumo_rows.append((f"fonte_{k}", v))

    desplan_count = int(df["is_desplanilhada"].sum()) if "is_desplanilhada" in df.columns else 0
    resumo_rows.append(("desplanilhadas", desplan_count))

    resumo_df = pd.DataFrame(resumo_rows, columns=["metrica", "valor"])

    # Build tabs
    tabs: dict[str, pd.DataFrame] = {"resumo": resumo_df}

    # Suspeitas: unknown + review_manual + desplanilhadas
    suspeitas_filter = ["REVISAO_MANUAL", "DESPLANILHADA"]
    tabs["suspeitas"] = _filter_tab(df, "veredito_final", suspeitas_filter)

    # Desplanilhadas only
    if "is_desplanilhada" in df.columns:
        tabs["desplanilhadas"] = df[df["is_desplanilhada"]].copy()
    else:
        tabs["desplanilhadas"] = pd.DataFrame()

    # Revisao manual
    tabs["revisao_manual"] = _filter_tab(df, "veredito_final", ["REVISAO_MANUAL"])

    # Corrections
    correction_verdicts = ["CORRIGIR_PARA_GREEN", "CORRIGIR_PARA_RED", "CORRIGIR_PARA_ANULADA"]
    tabs["corrigir_green_red"] = _filter_tab(df, "veredito_final", correction_verdicts)

    # Sem match externo
    if "resultado_externo" in df.columns:
        no_ext = df[df["resultado_externo"].fillna("").astype(str).isin(["", "unknown"])].copy()
        tabs["sem_match_externo"] = no_ext
    else:
        tabs["sem_match_externo"] = df.copy()

    # Auditadas com IA
    if "fonte_veredito_final" in df.columns:
        tabs["auditadas_com_ia"] = df[df["fonte_veredito_final"] == "ia"].copy()
    else:
        tabs["auditadas_com_ia"] = pd.DataFrame()

    # Base completa
    tabs["base_completa"] = df

    # Write Excel
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for sheet_name, tab_df in tabs.items():
            tab_df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

    # Write CSVs
    csv_paths: dict[str, str] = {}
    for tab_name, tab_df in tabs.items():
        csv_path = output_dir / f"{tab_name}.csv"
        tab_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        csv_paths[tab_name] = str(csv_path)

    # Write summary JSON
    payload = {
        **metadata,
        "excel_output": str(excel_path),
        "csv_outputs": csv_paths,
        "summary": dict(resumo_rows),
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    return {
        "excel_output": str(excel_path),
        "summary_json": str(json_path),
        "output_dir": str(output_dir),
    }
