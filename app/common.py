from __future__ import annotations

from app.components import (  # noqa: F401
    apply_chart_style,
    compact_table,
    inject_styles,
    load_mart,
    render_kpi_strip,
    render_page_header,
    render_section_note,
    show_missing_data_message,
)
from app.filters import (  # noqa: F401
    GlobalFilters,
    apply_global_filters,
    apply_market_labels,
)

# Re-export build_global_filters with load_mart pre-bound
from app.filters import build_global_filters as _build_global_filters
from app.formatting import (  # noqa: F401
    format_int,
    format_number,
    format_pct,
)
from app.translations import (  # noqa: F401
    ALERT_LABELS,
    LANG_OPTIONS,
    MARKET_LABELS,
    PROFILE_LABELS,
    SEVERITY_LABELS,
    SEVERITY_ORDER,
    TEXT,
    col_label,
    t,
    to_alert_label,
    to_market_label,
    to_profile_label,
    to_severity_label,
)


def build_global_filters() -> GlobalFilters:
    return _build_global_filters(load_mart)
