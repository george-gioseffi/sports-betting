"""Centralised configuration loaded from environment / .env file."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AuditConfig:
    # --- search ---
    search_provider: str = "off"  # off | csv | mock
    search_data_file: str | None = None

    # --- LLM ---
    llm_mode: str = "off"  # off | assisted | review_all_suspects | dual_review
    llm_provider: str = "openai"  # openai | anthropic | dual
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    max_llm_calls: int = 200
    min_confidence: float = 0.6

    # --- I/O ---
    input_file: str = ""
    output_dir: str = "outputs/bet_audit"
    sheet_name: str | None = None

    # --- filters ---
    date_from: str | None = None
    date_to: str | None = None
    only_issues: bool = False

    # --- misc ---
    verbose: bool = False

    @classmethod
    def from_env(cls, **overrides: object) -> AuditConfig:
        """Build config from environment variables, then override with kwargs."""
        env_map: dict[str, object] = {
            "search_provider": os.getenv("SEARCH_PROVIDER", "off"),
            "search_data_file": os.getenv("SEARCH_DATA_FILE"),
            "llm_mode": os.getenv("LLM_MODE", "off"),
            "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "max_llm_calls": int(os.getenv("MAX_LLM_CALLS", "200")),
            "min_confidence": float(os.getenv("MIN_CONFIDENCE", "0.6")),
        }
        env_map.update({k: v for k, v in overrides.items() if v is not None})
        return cls(**env_map)  # type: ignore[arg-type]

    @property
    def llm_enabled(self) -> bool:
        return self.llm_mode != "off"

    @property
    def search_enabled(self) -> bool:
        return self.search_provider != "off"

    def has_api_key(self, provider: str = "") -> bool:
        prov = provider or self.llm_provider
        if prov == "openai":
            return bool(self.openai_api_key)
        if prov == "anthropic":
            return bool(self.anthropic_api_key)
        if prov == "dual":
            return bool(self.openai_api_key) or bool(self.anthropic_api_key)
        return False
