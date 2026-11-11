"""
Shared reporting package for Automation Lab CI dashboards and HTML audit reports.
"""
from .base_report import BaseHTMLReport
from .charts import (
    draw_historical_trend_chart,
    draw_scenario_bars_chart,
    draw_stacked_layers_chart,
    draw_step_profile_chart,
)
from .constants import (
    ATOMIC_STRATEGIES,
    EXPECTED_TEMPLATES,
    FRONTENDS,
    FULL_FLOW_STEPS,
    FULL_STRATEGIES,
    HISTORY_CSV_FIELDNAMES,
    HISTORY_DIR,
    LAYER_COLORS,
    PLAYWRIGHT_ROOT,
    REPORTS_DIR,
    STRATEGIES,
    STRATEGY_COLORS,
    TEMPLATES_DIR,
)
from .telemetry_io import (
    aggregate_per_run_layers,
    compute_stats,
    file_to_base64,
    img_to_base64,
    load_jsonl_file,
    load_jsonl_glob,
    load_legacy_csv_history,
    percentile,
    read_png_info,
    summarize_cell_records,
)

__all__ = [
    "BaseHTMLReport",
    "ATOMIC_STRATEGIES",
    "EXPECTED_TEMPLATES",
    "FRONTENDS",
    "FULL_FLOW_STEPS",
    "FULL_STRATEGIES",
    "HISTORY_CSV_FIELDNAMES",
    "HISTORY_DIR",
    "LAYER_COLORS",
    "PLAYWRIGHT_ROOT",
    "REPORTS_DIR",
    "STRATEGIES",
    "STRATEGY_COLORS",
    "TEMPLATES_DIR",
    "aggregate_per_run_layers",
    "compute_stats",
    "draw_historical_trend_chart",
    "draw_scenario_bars_chart",
    "draw_stacked_layers_chart",
    "draw_step_profile_chart",
    "file_to_base64",
    "img_to_base64",
    "load_jsonl_file",
    "load_jsonl_glob",
    "load_legacy_csv_history",
    "percentile",
    "read_png_info",
    "summarize_cell_records",
]
