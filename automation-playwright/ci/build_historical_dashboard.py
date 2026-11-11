"""
Consolidate the last K executions per (strategy, frontend) cell from
`automation-playwright/metrics-history/` (`history_tests.jsonl`, `history_steps.jsonl`,
`history.csv`) and render a pure statistical & graphical HTML report
(`reports/historical_dashboard.html`) with 5 scientific Base64 PNG charts.
Decoupled from visual audit screenshots to avoid data/image duplication.
"""
import argparse
import html
import os
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

CI_DIR = Path(__file__).resolve().parent
if str(CI_DIR) not in sys.path:
    sys.path.insert(0, str(CI_DIR))

from reporting import (
    ATOMIC_STRATEGIES,
    FRONTENDS,
    FULL_STRATEGIES,
    HISTORY_DIR,
    REPORTS_DIR,
    STRATEGIES,
    BaseHTMLReport,
    compute_stats,
    draw_historical_trend_chart,
    draw_scenario_bars_chart,
    draw_stacked_layers_chart,
    draw_step_profile_chart,
    load_jsonl_file,
    load_legacy_csv_history,
    summarize_cell_records,
)


def _consolidate_historical_cells(
    window_size: int,
    hist_tests: List[Dict[str, Any]],
    hist_steps: List[Dict[str, Any]],
    legacy_csv_rows: List[Dict[str, Any]],
) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Consolidate the last `window_size` executions per `(strategy, frontend)` cell."""
    summary_by_cell: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for strat in STRATEGIES:
        for fe in FRONTENDS:
            cell_t_all = [r for r in hist_tests if r.get("strategy") == strat and r.get("frontend") == fe]
            passed_t = [r for r in cell_t_all if r.get("outcome") == "passed"]
            t_recs = (passed_t if passed_t else cell_t_all)[-window_size:]

            if t_recs:
                run_keys = {(r.get("run_id"), r.get("repeat_idx")) for r in t_recs}
                s_recs = [
                    r for r in hist_steps
                    if r.get("strategy") == strat
                    and r.get("frontend") == fe
                    and (r.get("run_id"), r.get("repeat_idx")) in run_keys
                ]

                jsonl_builds = {str(r.get("build_number", "")) for r in cell_t_all}
                needed = max(0, window_size - len(t_recs))
                extra_csv_all = [
                    r for r in legacy_csv_rows
                    if r.get("strategy") == strat
                    and r.get("frontend") == fe
                    and str(r.get("build_number", "")) not in jsonl_builds
                    and str(r.get("build_number", "")) != "local"
                ]
                extra_csv_passed = [r for r in extra_csv_all if float(r.get("passed", 0)) > 0]

                extra_totals: List[float] = []
                extra_calls: List[float] = []
                if needed > 0 and extra_csv_passed:
                    for er in extra_csv_passed[-needed:]:
                        extra_totals.append(float(er.get("total_median_ms", 0.0)))
                        extra_calls.append(float(er.get("call_median_ms", 0.0)))

                recent_all_cnt = len(cell_t_all[-window_size:]) + min(
                    needed, len(extra_csv_all[-needed:] if needed > 0 else [])
                )
                passed_cnt = sum(1 for r in cell_t_all[-window_size:] if r.get("outcome") == "passed") + min(
                    needed, len(extra_csv_passed[-needed:] if needed > 0 else [])
                )

                cell_summary = summarize_cell_records(
                    strat,
                    fe,
                    t_recs,
                    s_recs,
                    extra_total_times=extra_totals,
                    extra_call_times=extra_calls,
                    runs_override=recent_all_cnt,
                    passed_override=passed_cnt,
                )
                last_b = str(t_recs[-1].get("build_number", "local"))
                cell_summary["last_build"] = f"#{last_b}"
                summary_by_cell[(strat, fe)] = cell_summary
            else:
                csv_matches = [
                    r for r in legacy_csv_rows
                    if r.get("strategy") == strat and r.get("frontend") == fe and float(r.get("passed", 0)) > 0
                ][-window_size:]
                if csv_matches:
                    totals = [float(r["total_median_ms"]) for r in csv_matches]
                    steps_m = [float(r["step_median_ms"]) for r in csv_matches]
                    t_stats = compute_stats(totals)
                    s_stats = compute_stats(steps_m)
                    last_r = csv_matches[-1]
                    last_b = str(last_r.get("build_number", "local"))
                    summary_by_cell[(strat, fe)] = {
                        "strategy": strat,
                        "frontend": fe,
                        "runs": len(csv_matches),
                        "passed": len(csv_matches),
                        "pass_rate_pct": 100.0,
                        "total_median_ms": t_stats["median"],
                        "total_p95_ms": t_stats["p95"],
                        "total_mean_ms": t_stats["mean"],
                        "total_stdev_ms": t_stats["stdev"],
                        "call_median_ms": float(last_r.get("call_median_ms", 0.0)),
                        "step_median_ms": s_stats["median"],
                        "step_p95_ms": s_stats["p95"],
                        "capture_ms": float(last_r.get("capture_ms", 0.0)),
                        "network_ms": float(last_r.get("network_ms", 0.0)),
                        "decode_preprocess_ms": float(last_r.get("decode_preprocess_ms", 0.0)),
                        "template_ms": float(last_r.get("template_ms", 0.0)),
                        "ocr_ranking_ms": float(last_r.get("ocr_ranking_ms", 0.0)),
                        "mean_confidence": float(last_r.get("mean_confidence", 1.0)),
                        "dom_hit_rate_pct": float(last_r.get("dom_hit_rate_pct", 100.0)),
                        "last_build": f"#{last_b}",
                    }

    return summary_by_cell


class HistoricalDashboardReport(BaseHTMLReport):
    """Statistical & scientific HTML report consolidating historical runs from `metrics-history/`."""

    def __init__(
        self,
        window_size: int,
        summary_by_cell: Dict[Tuple[str, str], Dict[str, Any]],
        hist_steps: List[Dict[str, Any]],
        legacy_csv_rows: List[Dict[str, Any]],
    ) -> None:
        super().__init__()
        self.window_size = window_size
        self.summary_by_cell = summary_by_cell
        self.hist_steps = hist_steps
        self.legacy_csv_rows = legacy_csv_rows

    def page_title(self) -> str:
        return "Automation Lab — Dashboard Estadístico e Histórico de Tesis"

    def header_title(self) -> str:
        return "Automation Lab — Dashboard Estadístico e Histórico de Estrategias UI"

    def header_subtitle(self) -> str:
        return (
            f"Build #{html.escape(str(self.build_num))} | "
            f"Generado: {html.escape(self.now_iso)} | "
            f"Ventana Móvil: Últimas K={self.window_size} ejecuciones por celda (<code>metrics-history/</code>)"
        )

    def extra_css(self) -> str:
        return """
    th:nth-child(3), td:nth-child(3) { text-align: left; }
"""

    def _build_consolidated_table_rows(self) -> str:
        table_rows_html: List[str] = []
        for strat in STRATEGIES:
            for fe in FRONTENDS:
                cell = self.summary_by_cell.get((strat, fe))
                if not cell:
                    continue
                is_pass = cell["pass_rate_pct"] >= 100.0
                status_txt = f"{cell['pass_rate_pct']:.1f}% ({cell['passed']}/{cell['runs']})"
                table_rows_html.append(
                    f"""
                    <tr>
                      <td>{self.strat_pill(strat)}</td>
                      <td><b>{fe.capitalize()}</b></td>
                      <td><span class="src-pill">{html.escape(cell['last_build'])}</span></td>
                      <td>{cell['runs']}</td>
                      <td>{self.status_pill(status_txt, is_pass)}</td>
                      <td><b>{cell['total_median_ms']:.1f}</b></td>
                      <td>{cell['total_p95_ms']:.1f}</td>
                      <td>{cell['total_stdev_ms']:.1f}</td>
                      <td><b>{cell['step_median_ms']:.1f}</b></td>
                      <td>{cell['capture_ms']:.1f}</td>
                      <td>{cell['template_ms']:.1f}</td>
                      <td>{cell['ocr_ranking_ms']:.1f}</td>
                      <td>{cell['mean_confidence']:.3f}</td>
                      <td>{cell['dom_hit_rate_pct']:.0f}%</td>
                    </tr>
                    """
                )
        return (
            "\n".join(table_rows_html)
            if table_rows_html
            else '<tr><td colspan="14">No se encontraron registros en metrics-history/.</td></tr>'
        )

    def _build_full_flow_step_rows(self) -> str:
        full_step_rows_html: List[str] = []
        full_step_records = [r for r in self.hist_steps if r.get("strategy") in ("getby_full", "opencv_full")]
        if full_step_records:
            step_groups: Dict[Tuple[str, str, str], List[Dict[str, Any]]] = {}
            for r in full_step_records:
                k = (str(r.get("frontend", "")), str(r.get("step_name", "")), str(r.get("strategy", "")))
                step_groups.setdefault(k, []).append(r)

            for (fe, sname, strat), recs in sorted(step_groups.items()):
                recent_recs = recs[-self.window_size:]
                med_ms = statistics.median([float(x.get("total_step_ms", 0.0)) for x in recent_recs])
                tpl_ms = statistics.median([float(x.get("server_template_ms", 0.0)) for x in recent_recs])
                ocr_ms = statistics.median([float(x.get("server_ocr_ms", 0.0)) for x in recent_recs])
                conf_vals = [float(x["confidence_score"]) for x in recent_recs if x.get("confidence_score") is not None]
                mean_c = statistics.mean(conf_vals) if conf_vals else 1.0
                assertions = int(recent_recs[-1].get("visual_assertions_count") or 1)
                layer = str(recent_recs[-1].get("layer_resolved") or "")
                ocr_badge = (
                    "OCR=True"
                    if recent_recs[-1].get("enable_ocr")
                    else ("OCR=False" if strat == "opencv_full" else "DOM")
                )
                full_step_rows_html.append(
                    f"""
                    <tr>
                      <td>{self.strat_pill(strat)}</td>
                      <td><b>{fe.capitalize()}</b></td>
                      <td style="text-align:left"><code>{html.escape(sname)}</code></td>
                      <td><code>{html.escape(layer)}</code> ({ocr_badge})</td>
                      <td>{len(recent_recs)}</td>
                      <td>{assertions}</td>
                      <td><b>{med_ms:.1f}</b></td>
                      <td>{tpl_ms:.1f}</td>
                      <td>{ocr_ms:.1f}</td>
                      <td>{mean_c:.3f}</td>
                    </tr>
                    """
                )
        return (
            "\n".join(full_step_rows_html)
            if full_step_rows_html
            else '<tr><td colspan="10">No se encontraron registros paso a paso de flujos completos en metrics-history/.</td></tr>'
        )

    def build_body(self) -> str:
        chart_atomic_b64 = draw_scenario_bars_chart(
            "Gráfico 1: Escenario Atómico (base vs getby vs opencv) — Tiempo Total E2E Mediana + P95 (ms)",
            f"Comparativa sobre tests/test_products.py (Ventana histórica K={self.window_size} ejecuciones por celda)",
            ATOMIC_STRATEGIES,
            self.summary_by_cell,
            metric_key="total_median_ms",
            p95_key="total_p95_ms",
            show_overhead_ratio=False,
        )
        chart_full_b64 = draw_scenario_bars_chart(
            "Gráfico 2: Escenario Flujo E2E Completo 1:1 (getby_full vs opencv_full) — Mediana + P95 (ms)",
            "Flujo completo post-login de 5 pasos (Home -> Catálogo 2 ítems -> Carrito -> Eliminación -> Verificación)",
            FULL_STRATEGIES,
            self.summary_by_cell,
            metric_key="total_median_ms",
            p95_key="total_p95_ms",
            show_overhead_ratio=True,
        )
        chart_steps_b64 = draw_step_profile_chart(self.hist_steps)
        chart_layers_b64 = draw_stacked_layers_chart(self.summary_by_cell)
        chart_trend_b64 = draw_historical_trend_chart(self.legacy_csv_rows)

        rows_str = self._build_consolidated_table_rows()
        full_steps_str = self._build_full_flow_step_rows()

        return f"""
  <section class="card">
    <h2>1. Tabla Resumen Experimental Consolidada (Últimas K={self.window_size} Corridas por Estrategia y Frontend)</h2>
    <table>
      <thead>
        <tr>
          <th>Estrategia</th>
          <th>Frontend</th>
          <th>Últ. Build</th>
          <th>N (Ventana)</th>
          <th>Tasa Éxito</th>
          <th>Total Mediana (ms)</th>
          <th>Total p95 (ms)</th>
          <th>Total DE (ms)</th>
          <th>Acciones Total (ms)</th>
          <th>Captura (ms)</th>
          <th>TM_CCOEFF (ms)</th>
          <th>EasyOCR+Rank (ms)</th>
          <th>Confianza</th>
          <th>DOM Hit</th>
        </tr>
      </thead>
      <tbody>
        {rows_str}
      </tbody>
    </table>
  </section>

  <section class="card">
    <h2>2. Desglose Paso a Paso — Flujos E2E Completos Post-Login (<code>getby_full</code> vs <code>opencv_full</code>)</h2>
    <table>
      <thead>
        <tr>
          <th>Estrategia</th>
          <th>Frontend</th>
          <th style="text-align:left">Paso del Flujo E2E</th>
          <th>Capa / Modo OCR</th>
          <th>N</th>
          <th>Aserciones</th>
          <th>Mediana Paso (ms)</th>
          <th>TM_CCOEFF (ms)</th>
          <th>EasyOCR (ms)</th>
          <th>Confianza</th>
        </tr>
      </thead>
      <tbody>
        {full_steps_str}
      </tbody>
    </table>
  </section>

  <section class="card">
    <h2>3. Análisis Gráfico Comparativo, Desglose por Capa v1 y Tendencia Histórica</h2>
    <div class="charts-grid">
      <div class="chart-box">
        <img src="data:image/png;base64,{chart_atomic_b64}" alt="Gráfico 1: Escenario Atómico" />
      </div>
      <div class="chart-box">
        <img src="data:image/png;base64,{chart_full_b64}" alt="Gráfico 2: Escenario Flujo Completo" />
      </div>
      <div class="chart-box">
        <img src="data:image/png;base64,{chart_steps_b64}" alt="Gráfico 3: Perfil Paso a Paso y OCR Adaptativo" />
      </div>
      <div class="chart-box">
        <img src="data:image/png;base64,{chart_layers_b64}" alt="Gráfico 4: Desglose de Latencia por Capa" />
      </div>
      <div class="chart-box">
        <img src="data:image/png;base64,{chart_trend_b64}" alt="Gráfico 5: Evolución Histórica por Build" />
      </div>
    </div>
  </section>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Consolidate historical metrics and render 5 scientific charts.")
    parser.add_argument(
        "--window-size",
        type=int,
        default=int(os.getenv("METRICS_WINDOW_SIZE", "5")),
        help="Number of most recent executions per (strategy, frontend) cell to aggregate (default: 5)",
    )
    args = parser.parse_args()
    window_size = max(1, args.window_size)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    hist_tests = load_jsonl_file(HISTORY_DIR / "history_tests.jsonl")
    hist_steps = load_jsonl_file(HISTORY_DIR / "history_steps.jsonl")
    legacy_csv_rows = load_legacy_csv_history(HISTORY_DIR / "history.csv")

    summary_by_cell = _consolidate_historical_cells(
        window_size, hist_tests, hist_steps, legacy_csv_rows
    )

    report = HistoricalDashboardReport(window_size, summary_by_cell, hist_steps, legacy_csv_rows)
    out_path = report.save(REPORTS_DIR / "historical_dashboard.html")
    print(f"[Historical Dashboard] Generated {out_path} (window_size={window_size})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
