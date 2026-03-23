from __future__ import annotations

import argparse
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


PT_WEEKDAYS = {
    0: "segunda-feira",
    1: "terca-feira",
    2: "quarta-feira",
    3: "quinta-feira",
    4: "sexta-feira",
    5: "sabado",
    6: "domingo",
}

TIME_WINDOWS = [
    ("8h-12h", 8.0, 12.0),
    ("12h-14h", 12.0, 14.0),
    ("12h-16h", 12.0, 16.0),
    ("14h-18h", 14.0, 18.0),
    ("18h-22h", 18.0, 22.0),
    ("22h-0h", 22.0, 0.0),
    ("0h-6h", 0.0, 6.0),
    ("10h-14h", 10.0, 14.0),
]

COLUMN_SYNONYMS = {
    "data_hora": ["data", "date", "datetime", "data_hora", "datahora", "dia"],
    "horario": ["horario", "hora", "time"],
    "casa": [
        "casa",
        "bookmaker",
        "casa_de_aposta",
        "casa_de_apostas",
        "book",
        "operadora",
        "site",
    ],
    "status": ["estado", "status", "resultado", "result", "outcome"],
    "lucro": [
        "lucro",
        "profit",
        "pnl",
        "ganho_prejuizo",
        "retorno_liquido",
        "ganho",
        "prejuizo",
    ],
    "valor_apostado": [
        "valor",
        "valor_apostado",
        "stake_valor",
        "investimento",
        "amount",
    ],
    "stake": ["stake", "unidades", "units"],
    "odd": ["odd", "odds", "cotacao"],
    "descricao": ["aposta", "descricao", "mercado", "jogo", "evento", "selecao", "bet"],
}


def normalize_token(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def normalize_free_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = text.strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def to_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    s = series.astype(str).str.strip()
    s = s.str.replace("R$", "", regex=False)
    s = s.str.replace(" ", "", regex=False)
    s = s.replace({"": np.nan, "nan": np.nan, "none": np.nan})
    if s.isna().all():
        return pd.to_numeric(s, errors="coerce")
    has_comma = s.str.contains(",", na=False)
    has_dot = s.str.contains(r"\.", na=False)
    both = has_comma & has_dot
    s.loc[both] = s.loc[both].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    only_comma = has_comma & ~has_dot
    s.loc[only_comma] = s.loc[only_comma].str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def normalize_result_from_status(status: object) -> str:
    token = normalize_free_text(status)
    if not token:
        return "unknown"

    green_markers = ("ganh", "win", "green", "vitori", "halfwin", "meioganh", "meiaganh")
    red_markers = ("perd", "loss", "red", "derrot", "halfloss", "meioperd", "meiaperd")
    void_markers = ("anulad", "empate", "void", "push", "cancel", "refund", "reembols")

    if any(marker in token for marker in green_markers):
        return "green"
    if any(marker in token for marker in red_markers):
        return "red"
    if any(marker in token for marker in void_markers):
        return "void"
    return "unknown"


def normalize_result_final(status: object, lucro: float) -> str:
    from_status = normalize_result_from_status(status)
    if from_status != "unknown":
        return from_status

    if pd.notna(lucro):
        if lucro > 0:
            return "green"
        if lucro < 0:
            return "red"
        return "void"
    return "unknown"


def first_matching_column(columns: list[str], candidates: Iterable[str]) -> str | None:
    by_normalized = {normalize_token(col): col for col in columns}
    for candidate in candidates:
        normalized = normalize_token(candidate)
        if normalized in by_normalized:
            return by_normalized[normalized]
    return None


@dataclass
class SheetChoice:
    sheet_name: str
    score: float
    matched_groups: int
    rows_previewed: int


def score_sheet(df_preview: pd.DataFrame, sheet_name: str) -> SheetChoice:
    columns = list(df_preview.columns)
    matched = 0
    for group, candidates in COLUMN_SYNONYMS.items():
        if first_matching_column(columns, candidates) is not None:
            matched += 1

    score = matched * 10 + min(len(df_preview), 300) / 300.0
    return SheetChoice(
        sheet_name=sheet_name,
        score=score,
        matched_groups=matched,
        rows_previewed=len(df_preview),
    )


def choose_sheet(input_path: Path) -> tuple[str, list[SheetChoice], str]:
    workbook = pd.ExcelFile(input_path)
    assessments: list[SheetChoice] = []
    for sheet_name in workbook.sheet_names:
        preview = pd.read_excel(input_path, sheet_name=sheet_name, nrows=300)
        assessments.append(score_sheet(preview, sheet_name))

    assessments.sort(key=lambda item: (item.score, item.matched_groups, item.rows_previewed), reverse=True)
    chosen = assessments[0]

    if len(workbook.sheet_names) == 1:
        reason = (
            f"Aba unica encontrada: '{chosen.sheet_name}'. "
            "Ela contem os dados de apostas e todas as colunas principais."
        )
    else:
        reason = (
            f"Aba '{chosen.sheet_name}' escolhida por maior score ({chosen.score:.2f}), "
            f"com {chosen.matched_groups} grupos de colunas esperadas reconhecidos."
        )

    return chosen.sheet_name, assessments, reason


def normalize_bookmakers(series: pd.Series) -> tuple[pd.Series, pd.Series]:
    original = series.fillna("").astype(str).str.strip()
    original = original.str.replace(r"\s+", " ", regex=True)
    original = original.replace("", "desconhecida")

    key = original.str.lower()
    canonical_map = (
        pd.DataFrame({"orig": original, "key": key})
        .groupby("key")["orig"]
        .agg(lambda x: x.value_counts(dropna=False).index[0])
        .to_dict()
    )
    normalized = key.map(canonical_map)
    return key, normalized


def in_window(hour_decimal: pd.Series, start: float, end: float) -> pd.Series:
    if end > start:
        return (hour_decimal >= start) & (hour_decimal < end)
    return (hour_decimal >= start) | (hour_decimal < end)


def build_analysis(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    df_work = df.copy()
    original_cols = list(df_work.columns)

    resolved_cols = {
        "data_hora": first_matching_column(original_cols, COLUMN_SYNONYMS["data_hora"]),
        "horario": first_matching_column(original_cols, COLUMN_SYNONYMS["horario"]),
        "casa": first_matching_column(original_cols, COLUMN_SYNONYMS["casa"]),
        "status": first_matching_column(original_cols, COLUMN_SYNONYMS["status"]),
        "lucro": first_matching_column(original_cols, COLUMN_SYNONYMS["lucro"]),
        "valor_apostado": first_matching_column(original_cols, COLUMN_SYNONYMS["valor_apostado"]),
        "stake": first_matching_column(original_cols, COLUMN_SYNONYMS["stake"]),
        "odd": first_matching_column(original_cols, COLUMN_SYNONYMS["odd"]),
        "descricao": first_matching_column(original_cols, COLUMN_SYNONYMS["descricao"]),
    }

    missing_essential = [key for key in ["data_hora", "casa", "lucro"] if resolved_cols.get(key) is None]
    if missing_essential:
        raise ValueError(f"Colunas essenciais ausentes: {missing_essential}")

    out = pd.DataFrame()
    out["data_hora"] = pd.to_datetime(df_work[resolved_cols["data_hora"]], errors="coerce", dayfirst=True, format="mixed")
    out["casa_original"] = df_work[resolved_cols["casa"]].astype(str)
    out["lucro"] = to_numeric(df_work[resolved_cols["lucro"]])
    out["status_original"] = (
        df_work[resolved_cols["status"]].astype(str) if resolved_cols["status"] else pd.Series("", index=df_work.index)
    )
    out["descricao"] = (
        df_work[resolved_cols["descricao"]].astype(str)
        if resolved_cols["descricao"]
        else pd.Series("", index=df_work.index)
    )
    out["odd"] = to_numeric(df_work[resolved_cols["odd"]]) if resolved_cols["odd"] else np.nan
    out["valor_apostado"] = (
        to_numeric(df_work[resolved_cols["valor_apostado"]]) if resolved_cols["valor_apostado"] else np.nan
    )
    out["stake"] = to_numeric(df_work[resolved_cols["stake"]]) if resolved_cols["stake"] else np.nan

    # If date has no time and there is a dedicated time column, combine both.
    if resolved_cols["horario"]:
        time_series = pd.to_datetime(df_work[resolved_cols["horario"]].astype(str), errors="coerce")
        has_midnight_only = out["data_hora"].dt.hour.fillna(0).eq(0).all()
        has_valid_time = time_series.notna().any()
        if has_midnight_only and has_valid_time:
            out["data_hora"] = (
                out["data_hora"].dt.normalize()
                + pd.to_timedelta(time_series.dt.hour.fillna(0), unit="h")
                + pd.to_timedelta(time_series.dt.minute.fillna(0), unit="m")
                + pd.to_timedelta(time_series.dt.second.fillna(0), unit="s")
            )

    out["casa_original"] = out["casa_original"].fillna("").astype(str).str.strip()
    out["casa_original"] = out["casa_original"].str.replace(r"\s+", " ", regex=True)
    out["status_original"] = out["status_original"].fillna("").astype(str).str.strip()
    out["descricao"] = out["descricao"].fillna("").astype(str).str.strip()

    subtotal_text = (
        out["casa_original"].str.lower()
        + " "
        + out["status_original"].str.lower()
        + " "
        + out["descricao"].str.lower()
    )
    subtotal_mask = subtotal_text.str.contains(r"\btotal\b|\bsubtotal\b", na=False) & out["data_hora"].isna()
    out = out.loc[~subtotal_mask].copy()
    out = out.dropna(subset=["data_hora", "lucro"])

    _, out["casa"] = normalize_bookmakers(out["casa_original"])
    out["resultado_texto"] = out["status_original"].map(normalize_result_from_status)
    out["resultado_norm"] = [
        normalize_result_final(status, lucro)
        for status, lucro in zip(out["status_original"], out["lucro"], strict=False)
    ]

    out["is_green"] = out["resultado_norm"].eq("green")
    out["is_red"] = out["resultado_norm"].eq("red")
    out["is_void"] = out["resultado_norm"].eq("void")

    out["data"] = out["data_hora"].dt.date.astype(str)
    out["horario"] = out["data_hora"].dt.strftime("%H:%M:%S")
    out["mes"] = out["data_hora"].dt.to_period("M").astype(str)
    out["dia_semana_num"] = out["data_hora"].dt.weekday
    out["dia_semana"] = out["dia_semana_num"].map(PT_WEEKDAYS)
    out["hora_decimal"] = (
        out["data_hora"].dt.hour + out["data_hora"].dt.minute / 60.0 + out["data_hora"].dt.second / 3600.0
    )

    inconsist_status_lucro = (
        ((out["resultado_texto"] == "green") & (out["lucro"] <= 0))
        | ((out["resultado_texto"] == "red") & (out["lucro"] >= 0))
    ).sum()

    dias = (
        out.groupby(["dia_semana_num", "dia_semana"], as_index=False)
        .agg(
            lucro_total=("lucro", "sum"),
            quantidade_apostas=("lucro", "size"),
            media_lucro_por_aposta=("lucro", "mean"),
            greens=("is_green", "sum"),
            reds=("is_red", "sum"),
        )
        .sort_values(["lucro_total", "media_lucro_por_aposta"], ascending=False)
        .reset_index(drop=True)
    )
    dias["taxa_green_%"] = np.where(
        (dias["greens"] + dias["reds"]) > 0,
        dias["greens"] / (dias["greens"] + dias["reds"]) * 100.0,
        np.nan,
    )
    dias.insert(0, "ranking", np.arange(1, len(dias) + 1))

    casas_geral = (
        out.groupby("casa", as_index=False)
        .agg(
            lucro_total=("lucro", "sum"),
            quantidade_apostas=("lucro", "size"),
            media_lucro_por_aposta=("lucro", "mean"),
            greens=("is_green", "sum"),
            reds=("is_red", "sum"),
        )
        .sort_values(["lucro_total", "media_lucro_por_aposta"], ascending=False)
        .reset_index(drop=True)
    )
    casas_geral["taxa_green_%"] = np.where(
        (casas_geral["greens"] + casas_geral["reds"]) > 0,
        casas_geral["greens"] / (casas_geral["greens"] + casas_geral["reds"]) * 100.0,
        np.nan,
    )
    casas_geral.insert(0, "ranking", np.arange(1, len(casas_geral) + 1))

    casas_por_mes = (
        out.groupby(["mes", "casa"], as_index=False)
        .agg(
            lucro_total=("lucro", "sum"),
            quantidade_apostas=("lucro", "size"),
            media_lucro_por_aposta=("lucro", "mean"),
        )
        .sort_values(["mes", "lucro_total", "media_lucro_por_aposta"], ascending=[True, False, False])
        .reset_index(drop=True)
    )
    casas_por_mes["ranking_no_mes"] = (
        casas_por_mes.groupby("mes")["lucro_total"].rank(method="dense", ascending=False).astype(int)
    )

    lideres_mes = (
        casas_por_mes.loc[casas_por_mes["ranking_no_mes"] == 1, ["mes", "casa", "lucro_total"]]
        .sort_values("mes")
        .reset_index(drop=True)
    )

    pivot_casas_mes = pd.pivot_table(
        out,
        index="mes",
        columns="casa",
        values="lucro",
        aggfunc="sum",
        fill_value=0.0,
    ).sort_index()
    pivot_casas_mes = pivot_casas_mes.reset_index()

    red_mask = out["is_red"] | (out["lucro"] < 0)
    top_red = out.loc[red_mask].copy()
    top_red["prejuizo"] = top_red["lucro"]
    top_red["prejuizo_abs"] = top_red["lucro"].abs()
    top_red = top_red.sort_values(["prejuizo_abs", "prejuizo"], ascending=[False, True]).head(20)
    top_red = top_red[
        [
            "data",
            "horario",
            "casa",
            "descricao",
            "valor_apostado",
            "stake",
            "odd",
            "prejuizo",
            "status_original",
        ]
    ].reset_index(drop=True)
    top_red.insert(0, "ranking", np.arange(1, len(top_red) + 1))

    green_mask = out["is_green"] | (out["lucro"] > 0)
    top_green = out.loc[green_mask].copy()
    top_green = top_green.sort_values("lucro", ascending=False).head(20)
    top_green = top_green[
        [
            "data",
            "horario",
            "casa",
            "descricao",
            "valor_apostado",
            "stake",
            "odd",
            "lucro",
            "status_original",
        ]
    ].reset_index(drop=True)
    top_green.insert(0, "ranking", np.arange(1, len(top_green) + 1))

    faixa_rows: list[dict[str, object]] = []
    for name, start, end in TIME_WINDOWS:
        mask = in_window(out["hora_decimal"], start, end)
        subset = out.loc[mask]
        resolvidas = subset.loc[subset["resultado_norm"].isin(["green", "red"])]
        taxa_green = (
            (resolvidas["resultado_norm"] == "green").mean() * 100.0 if len(resolvidas) > 0 else np.nan
        )
        faixa_rows.append(
            {
                "faixa_horaria": name,
                "lucro_total": subset["lucro"].sum(),
                "quantidade_apostas": len(subset),
                "media_lucro_por_aposta": subset["lucro"].mean() if len(subset) else np.nan,
                "qtd_resolvidas": len(resolvidas),
                "taxa_green_%": taxa_green,
            }
        )
    faixas_horario = pd.DataFrame(faixa_rows).sort_values(
        ["lucro_total", "media_lucro_por_aposta"], ascending=False
    )
    faixas_horario = faixas_horario.reset_index(drop=True)
    faixas_horario.insert(0, "ranking", np.arange(1, len(faixas_horario) + 1))

    for table in [dias, casas_geral, casas_por_mes, lideres_mes, top_red, top_green, faixas_horario, pivot_casas_mes]:
        numeric_cols = table.select_dtypes(include=[np.number]).columns
        table[numeric_cols] = table[numeric_cols].round(2)

    lucro_total = round(out["lucro"].sum(), 2)
    melhor_dia = dias.iloc[0]["dia_semana"] if not dias.empty else None
    melhor_casa = casas_geral.iloc[0]["casa"] if not casas_geral.empty else None
    melhor_faixa = faixas_horario.iloc[0]["faixa_horaria"] if not faixas_horario.empty else None
    pior_faixa = faixas_horario.iloc[-1]["faixa_horaria"] if not faixas_horario.empty else None
    maior_red = top_red.iloc[0]["prejuizo"] if not top_red.empty else None
    maior_green = top_green.iloc[0]["lucro"] if not top_green.empty else None

    resumo_records = [
        ("total_apostas_validas", len(out)),
        ("periodo_inicial", out["data_hora"].min().isoformat(sep=" ")),
        ("periodo_final", out["data_hora"].max().isoformat(sep=" ")),
        ("lucro_total", lucro_total),
        ("quantidade_green", int(out["is_green"].sum())),
        ("quantidade_red", int(out["is_red"].sum())),
        ("quantidade_void", int(out["is_void"].sum())),
        ("melhor_dia_semana", melhor_dia),
        ("melhor_casa_geral", melhor_casa),
        ("melhor_faixa_horaria", melhor_faixa),
        ("pior_faixa_horaria", pior_faixa),
        ("maior_red", maior_red),
        ("maior_green", maior_green),
        ("inconsistencias_status_vs_lucro", int(inconsist_status_lucro)),
    ]
    resumo_df = pd.DataFrame(resumo_records, columns=["metrica", "valor"])

    return {
        "base_tratada": out,
        "resumo": resumo_df,
        "dias_semana": dias,
        "casas_geral": casas_geral,
        "casas_por_mes": casas_por_mes,
        "lideres_mes": lideres_mes,
        "pivot_casas_mes": pivot_casas_mes,
        "top_20_red": top_red,
        "top_20_green": top_green,
        "faixas_horario": faixas_horario,
    }


def export_outputs(
    output_dir: Path,
    analyses: dict[str, pd.DataFrame],
    input_file: Path,
    sheet_name: str,
    sheet_reason: str,
    sheet_scores: list[SheetChoice],
    resolved_columns: dict[str, str | None],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    excel_path = output_dir / f"analise_apostas_{timestamp}.xlsx"
    summary_json_path = output_dir / f"resumo_execucao_{timestamp}.json"

    workbook_sheets = {
        "resumo": analyses["resumo"],
        "dias_semana": analyses["dias_semana"],
        "casas_geral": analyses["casas_geral"],
        "casas_por_mes": analyses["casas_por_mes"],
        "top_20_red": analyses["top_20_red"],
        "top_20_green": analyses["top_20_green"],
        "faixas_horario": analyses["faixas_horario"],
        "lideres_mes": analyses["lideres_mes"],
        "pivot_casas_mes": analyses["pivot_casas_mes"],
    }

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for name, table in workbook_sheets.items():
            table.to_excel(writer, sheet_name=name, index=False)

    csv_paths: dict[str, str] = {}
    for name, table in workbook_sheets.items():
        csv_path = output_dir / f"{name}.csv"
        table.to_csv(csv_path, index=False, encoding="utf-8-sig")
        csv_paths[name] = str(csv_path)

    analyses["base_tratada"].to_csv(output_dir / "base_tratada.csv", index=False, encoding="utf-8-sig")

    summary_payload = {
        "input_file": str(input_file),
        "chosen_sheet": sheet_name,
        "sheet_reason": sheet_reason,
        "sheet_scores": [choice.__dict__ for choice in sheet_scores],
        "resolved_columns": resolved_columns,
        "rows_base_tratada": int(len(analyses["base_tratada"])),
        "period_start": str(analyses["base_tratada"]["data_hora"].min()),
        "period_end": str(analyses["base_tratada"]["data_hora"].max()),
        "excel_output": str(excel_path),
        "csv_outputs": csv_paths,
    }
    summary_json_path.write_text(json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "excel_output": str(excel_path),
        "summary_json": str(summary_json_path),
        "output_dir": str(output_dir),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analisa historico de apostas em Excel e gera relatorio completo.")
    parser.add_argument("--input", required=True, help="Caminho do arquivo Excel de historico.")
    parser.add_argument(
        "--output-dir",
        default="outputs_analise_apostas",
        help="Pasta para salvar o relatorio final e os CSVs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {input_path}")

    chosen_sheet, sheet_scores, sheet_reason = choose_sheet(input_path)
    raw_df = pd.read_excel(input_path, sheet_name=chosen_sheet)

    analyses = build_analysis(raw_df)
    resolved_columns = {
        logical_name: first_matching_column(list(raw_df.columns), candidates)
        for logical_name, candidates in COLUMN_SYNONYMS.items()
    }

    outputs = export_outputs(
        output_dir=output_dir,
        analyses=analyses,
        input_file=input_path,
        sheet_name=chosen_sheet,
        sheet_reason=sheet_reason,
        sheet_scores=sheet_scores,
        resolved_columns=resolved_columns,
    )

    print(json.dumps(
        {
            "status": "ok",
            "input_file": str(input_path),
            "chosen_sheet": chosen_sheet,
            "sheet_reason": sheet_reason,
            "output_dir": outputs["output_dir"],
            "excel_output": outputs["excel_output"],
            "summary_json": outputs["summary_json"],
        },
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
