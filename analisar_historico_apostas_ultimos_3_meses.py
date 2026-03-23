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


WEEKDAYS_PT = {
    0: "segunda-feira",
    1: "terca-feira",
    2: "quarta-feira",
    3: "quinta-feira",
    4: "sexta-feira",
    5: "sabado",
    6: "domingo",
}

TIME_WINDOWS = [
    ("0h-6h", 0.0, 6.0),
    ("8h-12h", 8.0, 12.0),
    ("12h-14h", 12.0, 14.0),
    ("12h-16h", 12.0, 16.0),
    ("16h-20h", 16.0, 20.0),
    ("20h-0h", 20.0, 0.0),
]

COLUMN_SYNONYMS = {
    "data_hora": ["data", "date", "datetime", "data_hora", "datahora"],
    "horario": ["horario", "hora", "time"],
    "casa": [
        "casa",
        "bookmaker",
        "casa_de_aposta",
        "casa_de_apostas",
        "operadora",
        "site",
    ],
    "status": ["estado", "status", "resultado", "result", "outcome"],
    "lucro": ["lucro", "profit", "pnl", "ganho", "prejuizo", "retorno_liquido"],
    "stake": ["stake", "unidades", "units"],
    "valor_apostado": ["valor", "valor_apostado", "amount", "investimento"],
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
    return re.sub(r"[^a-z0-9]+", "", text)


def first_matching_column(columns: list[str], candidates: Iterable[str]) -> str | None:
    normalized_map = {normalize_token(col): col for col in columns}
    for candidate in candidates:
        token = normalize_token(candidate)
        if token in normalized_map:
            return normalized_map[token]
    return None


def to_numeric(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    s = series.astype(str).str.strip()
    s = s.str.replace("R$", "", regex=False).str.replace(" ", "", regex=False)
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
    result_by_text = normalize_result_from_status(status)
    if result_by_text != "unknown":
        return result_by_text

    if pd.notna(lucro):
        if lucro > 0:
            return "green"
        if lucro < 0:
            return "red"
        return "void"
    return "unknown"


@dataclass
class SheetChoice:
    sheet_name: str
    score: float
    matched_groups: int
    rows_previewed: int


def score_sheet(df_preview: pd.DataFrame, sheet_name: str) -> SheetChoice:
    cols = list(df_preview.columns)
    matched = 0
    for candidates in COLUMN_SYNONYMS.values():
        if first_matching_column(cols, candidates) is not None:
            matched += 1

    score = matched * 10 + min(len(df_preview), 300) / 300
    return SheetChoice(sheet_name=sheet_name, score=score, matched_groups=matched, rows_previewed=len(df_preview))


def choose_sheet(input_path: Path) -> tuple[str, list[SheetChoice], str]:
    workbook = pd.ExcelFile(input_path)
    scores: list[SheetChoice] = []

    for sheet_name in workbook.sheet_names:
        preview = pd.read_excel(input_path, sheet_name=sheet_name, nrows=300)
        scores.append(score_sheet(preview, sheet_name))

    scores.sort(key=lambda x: (x.score, x.matched_groups, x.rows_previewed), reverse=True)
    chosen = scores[0]

    if len(workbook.sheet_names) == 1:
        reason = (
            f"Aba unica encontrada: '{chosen.sheet_name}'. "
            "Ela contem as colunas esperadas para data, casa, status, lucro, stake e odds."
        )
    else:
        reason = (
            f"Aba '{chosen.sheet_name}' escolhida por maior score ({chosen.score:.2f}), "
            f"com {chosen.matched_groups} grupos de colunas reconhecidos."
        )

    return chosen.sheet_name, scores, reason


def normalize_bookmakers(series: pd.Series) -> pd.Series:
    original = series.fillna("").astype(str).str.strip()
    original = original.str.replace(r"\s+", " ", regex=True)
    original = original.replace("", "desconhecida")

    key = original.str.lower()
    map_mode = (
        pd.DataFrame({"orig": original, "key": key})
        .groupby("key")["orig"]
        .agg(lambda x: x.value_counts().index[0])
        .to_dict()
    )
    return key.map(map_mode)


def in_window(hour_decimal: pd.Series, start: float, end: float) -> pd.Series:
    if end > start:
        return (hour_decimal >= start) & (hour_decimal < end)
    return (hour_decimal >= start) | (hour_decimal < end)


def prepare_base(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str | None], list[str]]:
    original_columns = list(raw_df.columns)
    resolved = {
        logical: first_matching_column(original_columns, synonyms)
        for logical, synonyms in COLUMN_SYNONYMS.items()
    }

    missing_essential = [col for col in ["data_hora", "casa", "lucro"] if resolved.get(col) is None]
    if missing_essential:
        raise ValueError(f"Colunas essenciais ausentes: {missing_essential}")

    base = pd.DataFrame()
    base["data_hora"] = pd.to_datetime(raw_df[resolved["data_hora"]], errors="coerce", dayfirst=True, format="mixed")
    base["casa_original"] = raw_df[resolved["casa"]].astype(str)
    base["lucro"] = to_numeric(raw_df[resolved["lucro"]])
    base["status_original"] = (
        raw_df[resolved["status"]].astype(str) if resolved["status"] else pd.Series("", index=raw_df.index)
    )
    base["descricao"] = (
        raw_df[resolved["descricao"]].astype(str) if resolved["descricao"] else pd.Series("", index=raw_df.index)
    )
    base["odd"] = to_numeric(raw_df[resolved["odd"]]) if resolved["odd"] else np.nan
    base["stake"] = to_numeric(raw_df[resolved["stake"]]) if resolved["stake"] else np.nan
    base["valor_apostado"] = (
        to_numeric(raw_df[resolved["valor_apostado"]]) if resolved["valor_apostado"] else np.nan
    )

    # If there is dedicated time and all datetime values are midnight, combine date + time.
    if resolved["horario"]:
        has_only_midnight = base["data_hora"].dt.hour.fillna(0).eq(0).all()
        time_raw = pd.to_datetime(raw_df[resolved["horario"]].astype(str), errors="coerce")
        if has_only_midnight and time_raw.notna().any():
            base["data_hora"] = (
                base["data_hora"].dt.normalize()
                + pd.to_timedelta(time_raw.dt.hour.fillna(0), unit="h")
                + pd.to_timedelta(time_raw.dt.minute.fillna(0), unit="m")
                + pd.to_timedelta(time_raw.dt.second.fillna(0), unit="s")
            )

    base["casa_original"] = base["casa_original"].fillna("").astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    base["status_original"] = base["status_original"].fillna("").astype(str).str.strip()
    base["descricao"] = base["descricao"].fillna("").astype(str).str.strip()

    subtotal_text = (
        base["casa_original"].str.lower() + " " + base["status_original"].str.lower() + " " + base["descricao"].str.lower()
    )
    subtotal_mask = subtotal_text.str.contains(r"\btotal\b|\bsubtotal\b", na=False) & base["data_hora"].isna()
    base = base.loc[~subtotal_mask].copy()
    base = base.dropna(subset=["data_hora", "lucro"])

    base["casa"] = normalize_bookmakers(base["casa_original"])
    base["resultado_texto"] = base["status_original"].map(normalize_result_from_status)
    base["resultado_norm"] = [
        normalize_result_final(status, lucro)
        for status, lucro in zip(base["status_original"], base["lucro"], strict=False)
    ]
    base["is_green"] = base["resultado_norm"].eq("green")
    base["is_red"] = base["resultado_norm"].eq("red")
    base["is_void"] = base["resultado_norm"].eq("void")

    base["data"] = base["data_hora"].dt.date.astype(str)
    base["horario"] = base["data_hora"].dt.strftime("%H:%M:%S")
    base["mes"] = base["data_hora"].dt.to_period("M").astype(str)
    base["dia_semana_num"] = base["data_hora"].dt.weekday
    base["dia_semana"] = base["dia_semana_num"].map(WEEKDAYS_PT)
    base["hora_decimal"] = (
        base["data_hora"].dt.hour + base["data_hora"].dt.minute / 60.0 + base["data_hora"].dt.second / 3600.0
    )

    # ROI uses stake; fallback to valor_apostado only where stake is missing.
    base["stake_roi"] = base["stake"]
    fallback_mask = base["stake_roi"].isna() & base["valor_apostado"].notna()
    base.loc[fallback_mask, "stake_roi"] = base.loc[fallback_mask, "valor_apostado"]

    assumptions: list[str] = []
    if fallback_mask.any():
        assumptions.append(
            f"{int(fallback_mask.sum())} linhas sem stake usaram valor_apostado como fallback para calculo de ROI."
        )
    if resolved["horario"] is None:
        assumptions.append("Nao havia coluna de horario separada; horario foi extraido da coluna de data_hora.")
    if resolved["descricao"] is None:
        assumptions.append("Nao havia coluna de descricao dedicada; descricao foi mantida vazia.")
    if not assumptions:
        assumptions.append("Nenhum fallback necessario para colunas essenciais.")

    return base, resolved, assumptions


def filter_last_n_months(base: pd.DataFrame, months: int = 3) -> tuple[pd.DataFrame, list[str], list[str]]:
    all_months = sorted(base["mes"].dropna().unique().tolist())
    selected = all_months[-months:] if len(all_months) >= months else all_months
    filtered = base[base["mes"].isin(selected)].copy()
    filtered = filtered.sort_values("data_hora").reset_index(drop=True)
    return filtered, selected, all_months


def safe_roi(lucro_sum: float, stake_sum: float) -> float:
    if pd.isna(stake_sum) or stake_sum == 0:
        return np.nan
    return lucro_sum / stake_sum


def build_analyses(filtered: pd.DataFrame) -> dict[str, pd.DataFrame]:
    data = filtered.copy()

    inconsistencies = (
        ((data["resultado_texto"] == "green") & (data["lucro"] <= 0))
        | ((data["resultado_texto"] == "red") & (data["lucro"] >= 0))
    ).sum()

    casas_mensais = (
        data.groupby(["mes", "casa"], as_index=False)
        .agg(
            lucro_total=("lucro", "sum"),
            quantidade_apostas=("lucro", "size"),
            media_lucro_por_aposta=("lucro", "mean"),
            stake_total=("stake_roi", "sum"),
        )
        .sort_values(["mes", "lucro_total", "media_lucro_por_aposta"], ascending=[True, False, False])
        .reset_index(drop=True)
    )
    casas_mensais["roi"] = [
        safe_roi(l, s) for l, s in zip(casas_mensais["lucro_total"], casas_mensais["stake_total"], strict=False)
    ]
    casas_mensais["ranking_no_mes"] = (
        casas_mensais.groupby("mes")["lucro_total"].rank(method="dense", ascending=False).astype(int)
    )

    lideres_mes = (
        casas_mensais.loc[casas_mensais["ranking_no_mes"] == 1, ["mes", "casa", "lucro_total"]]
        .sort_values("mes")
        .reset_index(drop=True)
    )

    pivot_casas_mensais = pd.pivot_table(
        data,
        index="mes",
        columns="casa",
        values="lucro",
        aggfunc="sum",
        fill_value=0.0,
    ).sort_index()
    pivot_casas_mensais = pivot_casas_mensais.reset_index()

    casas_geral = (
        data.groupby("casa", as_index=False)
        .agg(
            lucro_total=("lucro", "sum"),
            quantidade_apostas=("lucro", "size"),
            media_lucro_por_aposta=("lucro", "mean"),
            stake_total=("stake_roi", "sum"),
            greens=("is_green", "sum"),
            reds=("is_red", "sum"),
        )
        .sort_values(["lucro_total", "media_lucro_por_aposta"], ascending=False)
        .reset_index(drop=True)
    )
    casas_geral["green_rate_%"] = np.where(
        (casas_geral["greens"] + casas_geral["reds"]) > 0,
        casas_geral["greens"] / (casas_geral["greens"] + casas_geral["reds"]) * 100.0,
        np.nan,
    )
    casas_geral["roi"] = [
        safe_roi(l, s) for l, s in zip(casas_geral["lucro_total"], casas_geral["stake_total"], strict=False)
    ]
    casas_geral.insert(0, "ranking", np.arange(1, len(casas_geral) + 1))

    roi_green_mensal = (
        data.groupby("mes", as_index=False)
        .agg(
            quantidade_apostas=("lucro", "size"),
            greens=("is_green", "sum"),
            reds=("is_red", "sum"),
            stake_total=("stake_roi", "sum"),
            lucro_total=("lucro", "sum"),
        )
        .sort_values("mes")
        .reset_index(drop=True)
    )
    roi_green_mensal["green_rate_%"] = np.where(
        (roi_green_mensal["greens"] + roi_green_mensal["reds"]) > 0,
        roi_green_mensal["greens"] / (roi_green_mensal["greens"] + roi_green_mensal["reds"]) * 100.0,
        np.nan,
    )
    roi_green_mensal["roi"] = [
        safe_roi(l, s) for l, s in zip(roi_green_mensal["lucro_total"], roi_green_mensal["stake_total"], strict=False)
    ]

    melhor_mes_roi = (
        roi_green_mensal.sort_values("roi", ascending=False).iloc[0]["mes"] if not roi_green_mensal.empty else None
    )
    pior_mes_roi = (
        roi_green_mensal.sort_values("roi", ascending=True).iloc[0]["mes"] if not roi_green_mensal.empty else None
    )
    melhor_mes_greens = (
        roi_green_mensal.sort_values("greens", ascending=False).iloc[0]["mes"] if not roi_green_mensal.empty else None
    )

    red_mask = data["is_red"] | (data["lucro"] < 0)
    top_20_reds = data.loc[red_mask].copy()
    top_20_reds["prejuizo"] = top_20_reds["lucro"]
    top_20_reds["prejuizo_abs"] = top_20_reds["lucro"].abs()
    top_20_reds = top_20_reds.sort_values(["prejuizo_abs", "prejuizo"], ascending=[False, True]).head(20)
    top_20_reds = top_20_reds[
        ["data", "horario", "casa", "descricao", "stake", "odd", "prejuizo", "status_original"]
    ].reset_index(drop=True)
    top_20_reds.insert(0, "ranking", np.arange(1, len(top_20_reds) + 1))

    green_mask = data["is_green"] | (data["lucro"] > 0)
    top_20_greens = data.loc[green_mask].copy()
    top_20_greens = top_20_greens.sort_values("lucro", ascending=False).head(20)
    top_20_greens = top_20_greens[
        ["data", "horario", "casa", "descricao", "stake", "odd", "lucro", "status_original"]
    ].reset_index(drop=True)
    top_20_greens.insert(0, "ranking", np.arange(1, len(top_20_greens) + 1))

    melhor_dia = (
        data.groupby(["dia_semana_num", "dia_semana"], as_index=False)
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
    melhor_dia["green_rate_%"] = np.where(
        (melhor_dia["greens"] + melhor_dia["reds"]) > 0,
        melhor_dia["greens"] / (melhor_dia["greens"] + melhor_dia["reds"]) * 100.0,
        np.nan,
    )
    melhor_dia.insert(0, "ranking", np.arange(1, len(melhor_dia) + 1))

    faixa_rows: list[dict[str, object]] = []
    for faixa, start, end in TIME_WINDOWS:
        mask = in_window(data["hora_decimal"], start, end)
        subset = data.loc[mask]
        greens = int(subset["is_green"].sum())
        reds = int(subset["is_red"].sum())
        lucro_total = float(subset["lucro"].sum())
        stake_total = float(subset["stake_roi"].sum())
        faixa_rows.append(
            {
                "faixa_horaria": faixa,
                "lucro_total": lucro_total,
                "quantidade_apostas": len(subset),
                "media_lucro_por_aposta": subset["lucro"].mean() if len(subset) else np.nan,
                "greens": greens,
                "reds": reds,
                "green_rate_%": (greens / (greens + reds) * 100.0) if (greens + reds) > 0 else np.nan,
                "stake_total": stake_total,
                "roi": safe_roi(lucro_total, stake_total),
            }
        )

    faixas_horario = pd.DataFrame(faixa_rows).sort_values(
        ["lucro_total", "media_lucro_por_aposta"], ascending=False
    ).reset_index(drop=True)
    faixas_horario.insert(0, "ranking", np.arange(1, len(faixas_horario) + 1))

    resumo = pd.DataFrame(
        [
            ("total_apostas_filtradas", len(data)),
            ("periodo_inicial_filtrado", data["data_hora"].min().isoformat(sep=" ")),
            ("periodo_final_filtrado", data["data_hora"].max().isoformat(sep=" ")),
            ("lucro_total_3_meses", round(data["lucro"].sum(), 2)),
            ("greens_total_3_meses", int(data["is_green"].sum())),
            ("reds_total_3_meses", int(data["is_red"].sum())),
            ("melhor_casa_geral", casas_geral.iloc[0]["casa"] if not casas_geral.empty else None),
            ("melhor_dia_semana", melhor_dia.iloc[0]["dia_semana"] if not melhor_dia.empty else None),
            ("melhor_faixa_horaria", faixas_horario.iloc[0]["faixa_horaria"] if not faixas_horario.empty else None),
            ("melhor_mes_roi", melhor_mes_roi),
            ("pior_mes_roi", pior_mes_roi),
            ("melhor_mes_em_greens", melhor_mes_greens),
            ("maior_red", top_20_reds.iloc[0]["prejuizo"] if not top_20_reds.empty else None),
            ("maior_green", top_20_greens.iloc[0]["lucro"] if not top_20_greens.empty else None),
            ("inconsistencias_status_vs_lucro", int(inconsistencies)),
        ],
        columns=["metrica", "valor"],
    )

    tables = {
        "resumo": resumo,
        "casas_mensais": casas_mensais,
        "casas_geral": casas_geral,
        "roi_green_mensal": roi_green_mensal,
        "top_20_reds": top_20_reds,
        "top_20_greens": top_20_greens,
        "melhor_dia": melhor_dia,
        "faixas_horario": faixas_horario,
        "pivot_casas_mensais": pivot_casas_mensais,
        "lideres_mensais": lideres_mes,
        "base_filtrada": data,
    }

    for name, table in tables.items():
        if name == "base_filtrada":
            continue
        num_cols = table.select_dtypes(include=[np.number]).columns
        table[num_cols] = table[num_cols].round(4)

    return tables


def export_results(
    output_dir: Path,
    tables: dict[str, pd.DataFrame],
    metadata: dict[str, object],
) -> dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = output_dir / f"analise_ultimos_3_meses_{ts}.xlsx"
    json_path = output_dir / f"resumo_execucao_ultimos_3_meses_{ts}.json"

    excel_sheets = {
        "resumo": tables["resumo"],
        "casas_mensais": tables["casas_mensais"],
        "casas_geral": tables["casas_geral"],
        "roi_green_mensal": tables["roi_green_mensal"],
        "top_20_reds": tables["top_20_reds"],
        "top_20_greens": tables["top_20_greens"],
        "melhor_dia": tables["melhor_dia"],
        "faixas_horario": tables["faixas_horario"],
        "pivot_casas_mensais": tables["pivot_casas_mensais"],
        "lideres_mensais": tables["lideres_mensais"],
    }

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        for sheet_name, df in excel_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    csv_paths: dict[str, str] = {}
    for name, df in excel_sheets.items():
        csv_path = output_dir / f"{name}.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        csv_paths[name] = str(csv_path)

    base_csv = output_dir / "base_filtrada_ultimos_3_meses.csv"
    tables["base_filtrada"].to_csv(base_csv, index=False, encoding="utf-8-sig")

    payload = {**metadata, "excel_output": str(excel_path), "csv_outputs": csv_paths, "base_csv": str(base_csv)}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    return {"excel_output": str(excel_path), "summary_json": str(json_path), "output_dir": str(output_dir)}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analise de historico de apostas considerando apenas os ultimos 3 meses disponiveis."
    )
    parser.add_argument("--input", required=True, help="Arquivo Excel de entrada.")
    parser.add_argument("--output-dir", default="outputs/analise_ultimos_3_meses", help="Pasta de saida.")
    parser.add_argument(
        "--months",
        type=int,
        default=3,
        help="Quantidade de meses mais recentes para considerar (padrao: 3).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {input_path}")

    chosen_sheet, sheet_scores, sheet_reason = choose_sheet(input_path)
    raw = pd.read_excel(input_path, sheet_name=chosen_sheet)

    base, resolved_columns, assumptions = prepare_base(raw)
    filtered, selected_months, all_months = filter_last_n_months(base, months=args.months)
    tables = build_analyses(filtered)

    metadata = {
        "input_file": str(input_path),
        "chosen_sheet": chosen_sheet,
        "sheet_reason": sheet_reason,
        "resolved_columns": resolved_columns,
        "assumptions": assumptions,
        "available_months": all_months,
        "selected_months": selected_months,
        "selected_months_count": len(selected_months),
        "all_months_count": len(all_months),
        "rows_full_base": int(len(base)),
        "rows_filtered": int(len(filtered)),
        "period_filtered_start": str(filtered["data_hora"].min()),
        "period_filtered_end": str(filtered["data_hora"].max()),
        "sheet_scores": [s.__dict__ for s in sheet_scores],
    }

    outputs = export_results(output_dir=output_dir, tables=tables, metadata=metadata)

    print(
        json.dumps(
            {
                "status": "ok",
                "input_file": str(input_path),
                "chosen_sheet": chosen_sheet,
                "selected_months": selected_months,
                "output_dir": outputs["output_dir"],
                "excel_output": outputs["excel_output"],
                "summary_json": outputs["summary_json"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
