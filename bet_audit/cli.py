"""CLI entry point for bet_audit."""
from __future__ import annotations

import argparse
import json
import sys

from bet_audit.config import AuditConfig
from bet_audit.pipeline import run_audit


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="bet_audit",
        description="Auditor de apostas esportivas — valida planilhas com search externo, IA e regras.",
    )

    # Required
    p.add_argument("--input", required=True, help="Caminho do arquivo Excel de entrada.")

    # Output
    p.add_argument("--output", default="outputs/bet_audit", help="Pasta de saida.")

    # Search
    p.add_argument(
        "--search-provider", choices=["off", "csv", "mock"], default=None,
        help="Provider de busca externa (off|csv|mock).",
    )
    p.add_argument("--search-data-file", default=None, help="CSV de resultados externos.")

    # AI
    p.add_argument("--use-ai", action="store_true", help="Ativar classificacao por IA.")
    p.add_argument(
        "--llm-provider", choices=["openai", "anthropic", "dual"], default=None,
        help="Provider LLM (openai|anthropic|dual).",
    )
    p.add_argument(
        "--llm-mode", choices=["off", "assisted", "review_all_suspects", "dual_review"], default=None,
        help="Modo de uso da IA.",
    )

    # Filters
    p.add_argument("--date-from", default=None, help="Data inicial (YYYY-MM-DD).")
    p.add_argument("--date-to", default=None, help="Data final (YYYY-MM-DD).")
    p.add_argument("--only-issues", action="store_true", help="Exportar somente linhas com problemas.")
    p.add_argument("--sheet", default=None, help="Nome da aba do Excel para usar.")

    # Misc
    p.add_argument("--verbose", action="store_true", help="Modo verboso.")

    return p


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    overrides: dict[str, object] = {
        "input_file": args.input,
        "output_dir": args.output,
        "search_data_file": args.search_data_file,
        "date_from": args.date_from,
        "date_to": args.date_to,
        "only_issues": args.only_issues,
        "sheet_name": args.sheet,
        "verbose": args.verbose,
    }

    if args.search_provider is not None:
        overrides["search_provider"] = args.search_provider

    if args.use_ai:
        overrides["llm_mode"] = args.llm_mode or "assisted"
    elif args.llm_mode is not None:
        overrides["llm_mode"] = args.llm_mode

    if args.llm_provider is not None:
        overrides["llm_provider"] = args.llm_provider

    config = AuditConfig.from_env(**overrides)
    outputs = run_audit(config)

    print(json.dumps(
        {
            "status": "ok",
            "output_dir": outputs["output_dir"],
            "excel_output": outputs["excel_output"],
            "summary_json": outputs["summary_json"],
        },
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
